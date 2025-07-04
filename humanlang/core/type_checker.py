import re
from .structures import TypeSystemError, Environment

class TypeChecker:
    def __init__(self, interpreter):
        self.interpreter = interpreter

    def check(self, blocks, env):

        #Recursively traverses the code blocks to perform type checking.

        for stmt in blocks:
            if isinstance(stmt, list):
                head = stmt[0].lower().strip()
                if head.startswith('if'):
                    self.check_if(stmt, env)
                elif head.startswith('while'):
                    self.check_while(stmt, env)
                elif head.startswith('for each'):
                    self.check_for(stmt, env)
                # Class and task definitions are checked via their usage, not directly here.
            else:
                self.check_line(stmt, env)

    def check_line(self, line, env):

        #Dispatches a single line to the appropriate type-checking handler.
  
        line = line.strip()
        # Skip lines that don't need type-checking at this stage.
        if not line or line.startswith(('#', 'define', 'use', 'end', 'return', 'it has a property')):
            return

        if line.lower().startswith("declare"):
            match = re.match(r'declare (\w+) as a (.+)', line, re.I)
            if not match:
                raise TypeSystemError(f"Invalid declaration syntax: '{line}'")
            var, type_name = match.groups()
            env.declare(var, type_name.strip())

        elif line.lower().startswith("set"):
            self.check_set(line, env)

        elif line.lower().startswith("perform"):
            # Getting the expression type of a 'perform' statement implicitly checks
            # the existence and return type of the task.
            self.get_expression_type(line, env)
        
        elif line.lower().startswith("create a new"):
            # Checks if the class exists.
            match = re.match(r'create a new "([^"]+)"', line, re.I)
            class_name = match.group(1)
            if class_name not in self.interpreter.classes:
                raise TypeSystemError(f"Attempted to create an instance of an unknown class '{class_name}'.")


    def check_set(self, line, env):

        #Ensures that a variable or property assignment is type-safe.

        prop_match = re.match(r"set (\w+)'s (\w+) to (.+)", line, re.I)
        this_match = re.match(r"set this's (\w+) to (.+)", line, re.I)
        var_match = re.match(r'set (\w+) to (.+)', line, re.I)

        if prop_match:
            obj_name, prop, expr = prop_match.groups()
            obj_type_name = self.get_expression_type(obj_name, env)
            class_def = self.interpreter.classes.get(obj_type_name)

            if not class_def:
                raise TypeSystemError(f"Cannot set property on a non-class variable '{obj_name}' of type '{obj_type_name}'.")
            
            expected_type = class_def.properties.get(prop)
            if not expected_type:
                raise TypeSystemError(f"Class '{obj_type_name}' has no declared property named '{prop}'.")
            
            actual_type = self.get_expression_type(expr, env)
            if actual_type != "any" and expected_type != actual_type:
                raise TypeSystemError(f"Cannot assign type '{actual_type}' to property '{prop}' of type '{expected_type}'.")
        
        elif this_match:
            prop, expr = this_match.groups()
            this_type_name = env.get_type('this')
            class_def = self.interpreter.classes.get(this_type_name)
            if not class_def:
                raise TypeSystemError("'this' can only be used inside a class method.")

            expected_type = class_def.properties.get(prop)
            if not expected_type:
                raise TypeSystemError(f"Class '{this_type_name}' has no declared property named '{prop}'.")

            actual_type = self.get_expression_type(expr, env)
            if actual_type != "any" and expected_type != actual_type:
                raise TypeSystemError(f"Cannot assign type '{actual_type}' to property '{prop}' of type '{expected_type}'.")

        elif var_match:
            var, expr = var_match.groups()
            expected_type = env.get_type(var)
            if expected_type == "any":  # This is a dynamically typed variable, so no check is needed.
                return

            actual_type = self.get_expression_type(expr, env)
            if actual_type != "any" and expected_type != actual_type:
                raise TypeSystemError(f"Cannot assign expression of type '{actual_type}' to variable '{var}' of type '{expected_type}'.")

    def get_expression_type(self, expr, env):

        expr = expr.strip()

        # Literals
        if expr.isdigit() or (expr.startswith('-') and expr[1:].isdigit()):
            return "Number"
        if expr.startswith('"') and expr.endswith('"'):
            return "String"
        if expr.lower() in ["true", "false"]:
            return "Boolean"

        # Infix Expressions
        if " plus " in expr or " minus " in expr or " times " in expr or " divided by " in expr:
            # A more robust checker would verify that both operands are Numbers.
            return "Number"
        if " is greater than " in expr or " is less than " in expr or " is equal to " in expr or " and " in expr or " or " in expr:
            return "Boolean"
        if expr.lower().startswith("not "):
            return "Boolean"

        # Property Access
        prop_match = re.fullmatch(r"(\w+)'s (\w+)", expr, re.I)
        if prop_match:
            obj_name, prop_name = prop_match.groups()
            obj_type_name = self.get_expression_type(obj_name, env)
            class_def = self.interpreter.classes.get(obj_type_name)
            if not class_def:
                raise TypeSystemError(f"Cannot access property on non-class variable '{obj_name}' of type '{obj_type_name}'.")
            prop_type = class_def.properties.get(prop_name)
            if not prop_type:
                raise TypeSystemError(f"Class '{obj_type_name}' has no declared property '{prop_name}'.")
            return prop_type
        
        # Task/Method Call
        perform_match = re.match(r'perform "([^"]+)"', expr, re.I)
        if perform_match:
            task_name = perform_match.group(1)
            task = self.interpreter.global_tasks.get(task_name)
            if task:
                return task.get('returns', 'any')
            else:
                raise TypeSystemError(f"Attempted to call an unknown global task '{task_name}'.")
        
        # Simple variable lookup
        if re.fullmatch(r'\w+', expr):
            var_type = env.get_type(expr)
            if var_type != "any":
                return var_type

        return "any"

    def check_if(self, block, env):

        condition_str = re.match(r'if (.+) then', block[0], re.I).group(1)
        condition_type = self.get_expression_type(condition_str, env)
        if condition_type not in ["Boolean", "any"]:
            raise TypeSystemError(f"If condition must be a Boolean, but it is of type '{condition_type}'.")
        
        # Check the 'then' and 'else' bodies within the current scope.
        self.check(block[1:], env)

    def check_while(self, block, env):

        condition_str = re.match(r'while (.+) is true', block[0], re.I).group(1)
        condition_type = self.get_expression_type(condition_str, env)
        if condition_type not in ["Boolean", "any"]:
            raise TypeSystemError(f"While loop condition must be a Boolean, but it is of type '{condition_type}'.")

        # Check the loop body within the current scope.
        self.check(block[1:], env)

    def check_for(self, block, env):

        match = re.match(r'for each (\w+) in (\w+)', block[0], re.I)
        if not match:
             raise TypeSystemError(f"Invalid for loop syntax: '{block[0]}'")
        item_var, list_var = match.groups()

        list_type_str = self.get_expression_type(list_var, env)
        item_type = "any"

        # Check for typed list syntax like "List of Number"
        list_match = re.match(r'List of (\w+)', list_type_str, re.I)
        if list_match:
            item_type = list_match.group(1)
        
        # Create a new scope for the loop body where the item variable is declared.
        loop_env = Environment(outer=env)
        loop_env.declare(item_var, item_type)
        
        # Check the loop body with the new scope.
        self.check(block[1:], loop_env)
