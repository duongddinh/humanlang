import os
import re
import sys
import asyncio
from .structures import Environment, ClassDefinition, ObjectInstance, ReturnValue, TypeSystemError
from .parser import parse_code
from .type_checker import TypeChecker
from .executor import Executor

class HumanLang:
    def __init__(self):
        self.global_env = Environment()
        self.classes = {}
        self.global_tasks = {}
        self._imported_libs = set()
        self.type_checker = TypeChecker(self)
        self.executor = Executor(self)

    async def run_from_file(self, filepath):
        abs_filepath = os.path.abspath(filepath)
        if abs_filepath in self._imported_libs:
            return
        self._imported_libs.add(abs_filepath)
        base_dir = os.path.dirname(abs_filepath)
        try:
            with open(abs_filepath, 'r') as f:
                lines = [line.strip().rstrip('.') for line in f if line.strip()]
            code_blocks = parse_code(lines)
            await self.pre_process(code_blocks, base_dir)
            self.type_checker.check(code_blocks, self.global_env)
            print("Type checking passed successfully.")
            await self.executor.execute(code_blocks, self.global_env)
        except (TypeSystemError, NameError, ValueError, TypeError, SyntaxError, AttributeError) as e:
            print(f"Error: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Fatal Error: File not found at '{filepath}'")
            sys.exit(1)

    async def pre_process(self, blocks, base_dir):
        for item in blocks:
            if isinstance(item, list):
                head = item[0].lower().strip()
                if head.startswith('define a class'):
                    self.handle_define_class(item)
                elif head.startswith(('define a task', 'define an asynchronous task')):
                    self.handle_define_task(item, self.global_tasks)
                await self.pre_process(item[1:], base_dir)
            elif isinstance(item, str) and item.lower().startswith('use the library'):
                await self.handle_library_import(item, base_dir)

    def handle_define_class(self, block):
        match = re.match(r'define a class named "([^"]+)"(?: that inherits from "([^"]+)")?', block[0], re.I)
        class_name, parent_name = match.groups()
        parent_class = self.classes.get(parent_name) if parent_name else None
        class_def = ClassDefinition(class_name, parent_class)
        for item in block[1:]:
            if isinstance(item, str) and item.lower().strip().startswith("it has a property"):
                prop_match = re.match(r'it has a property named "([^"]+)" of type (.+)', item, re.I)
                prop_name, prop_type = prop_match.groups()
                class_def.properties[prop_name] = prop_type.strip()
            elif isinstance(item, list) and item[0].lower().strip().startswith("define"):
                self.handle_define_task(item, class_def.methods)
        self.classes[class_name] = class_def

    def handle_define_task(self, block, task_dict):
        full_def_line = block[0]
        is_async = "asynchronous" in full_def_line.lower()
        name_match = re.search(r'task named "([^"]+)"', full_def_line, re.I)
        name = name_match.group(1)
        params_str_match = re.search(r'that accepts (.+?)(?:\s+and returns|\s*$)', full_def_line, re.I)
        returns_match = re.search(r'and returns a (.+)', full_def_line, re.I)
        params_str = params_str_match.group(1) if params_str_match else None
        return_type = returns_match.group(1).strip() if returns_match else 'any'
        params = []
        if params_str:
            for p_def in params_str.split(','):
                p_match = re.match(r'"([^"]+)" of type (.+)', p_def.strip(), re.I)
                if not p_match: raise SyntaxError(f"Invalid parameter definition in task '{name}': {p_def}")
                p_name, p_type = p_match.groups()
                params.append({'name': p_name, 'type': p_type.strip()})
        task_dict[name] = {'params': params, 'body': block[1:], 'returns': return_type, 'is_async': is_async}

    async def handle_library_import(self, line, base_dir):
        match = re.match(r'use the library "([^"]+)"', line, re.I)
        if not match: return
        lib_path = os.path.join(base_dir, match.group(1))
        lib_interp = HumanLang()
        lib_interp._imported_libs = self._imported_libs
        await lib_interp.run_from_file(lib_path)
        self.classes.update(lib_interp.classes)
        self.global_tasks.update(lib_interp.global_tasks)

    async def _call_method(self, instance, method_name, args_str, calling_env, start_class=None):
        cls_to_search = start_class or instance.class_def
        method = cls_to_search.find_method(method_name)
        if not method: raise NameError(f"Method '{method_name}' not found in class '{instance.class_def.name}'.")
        method_env = Environment(outer=self.global_env)
        method_env.set('this', instance, instance.class_def.name)
        return await self._call_task_or_method(method, args_str, calling_env, method_env)

    async def _call_task_or_method(self, task_def, args_str, calling_env, execution_env):
        if not execution_env:
            execution_env = Environment(outer=self.global_env)
        args = re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', args_str) if args_str else []
        if len(args) != len(task_def['params']):
            raise ValueError(f"Incorrect number of arguments for task. Expected {len(task_def['params'])}, got {len(args)}.")
        for param_def, arg_expr in zip(task_def['params'], args):
            param_name, param_type = param_def['name'], param_def['type']
            arg_value = await self.eval_expr(arg_expr.strip(), calling_env)
            execution_env.set(param_name, arg_value, param_type)
        try:
            await self.executor.execute(task_def['body'], execution_env)
        except ReturnValue as rv:
            return rv.value
        return None
        
    def _prepare_expr_string(self, expr, env):
        self._current_eval_env = env
        
        # Use a more specific regex that is less likely to match inside strings
        # It looks for a variable name that isn't preceded by a quote character.
        e = re.sub(r"(?<!['\"])(\b\w+'s\s*[\w\']+\b)", lambda m: self._sub_property(m), expr, flags=re.I)
        e = re.sub(r"\bthis's\s*([\w\']+)\b", lambda m: self._sub_property(m, this_obj=env.get('this')), e, flags=re.I)

        all_vars = {}
        curr_env = env
        while curr_env:
            for k, v in curr_env.values.items():
                if k not in all_vars: all_vars[k] = v
            curr_env = curr_env.outer
            
        for var in sorted(all_vars.keys(), key=len, reverse=True):
            e = re.sub(rf'\b{var}\b', lambda m: repr(all_vars.get(m.group(0))), e)
        
        replacements = {
            " is greater than ": " > ", " is less than ": " < ", " is equal to ": " == ",
            " is not equal to ": " != ", " plus ": " + ", " minus ": " - ",
            " times ": " * ", " divided by ": " / ", " and ": " and ", " or ": " or ",
            " is true": " == True", " is false": " == False", " not ": " not "
        }
        for word, symbol in replacements.items():
            e = e.replace(word, symbol)
        return e

    async def eval_expr(self, expr, env):
        stripped_expr = expr.strip()
        # Directly return a variable if the expression is just its name.
        if re.fullmatch(r'\w+', stripped_expr):
            val = env.get(stripped_expr)
            if val is not None:
                return val

        # If it's a more complex expression, proceed with processing.
        processed_expr = self._prepare_expr_string(stripped_expr, env)
        safe_globals = {"__builtins__": {}, "True": True, "False": False}
        try:
            return eval(processed_expr, safe_globals)
        except TypeError as e:
            if "can only concatenate str" in str(e):
                try:
                    parts = processed_expr.split('+')
                    resolved_parts = [eval(part.strip(), safe_globals) for part in parts]
                    return "".join(map(str, resolved_parts))
                except Exception:
                    raise e
            else:
                raise e
        except Exception:
            try:
                original_expr = stripped_expr
                first_quote = original_expr.index('"')
                last_quote = original_expr.rindex('"')
                if first_quote < last_quote:
                    return original_expr[first_quote+1:last_quote]
            except ValueError:
                pass
            return stripped_expr.strip("'\"")

    def _sub_property(self, match, this_obj=None):
        original_text = match.group(0)
        
        if this_obj:
            obj = this_obj
            path_str = match.group(1)
        else:
            obj_name = original_text.split("'s")[0]
            obj = self._current_eval_env.get(obj_name)
            if obj is None:
                return original_text
            path_str = "'s".join(original_text.split("'s")[1:])

        keys = path_str.strip().split("'s")
        val = obj
        for key in keys:
            key = key.strip().lower()

            if val is None:
                break

            if key == 'length' and hasattr(val, '__len__'):
                val = len(val)
            elif isinstance(val, ObjectInstance):
                val = val.env.get(key)
            elif isinstance(val, dict):
                val = val.get(key)
            elif hasattr(val, key):
                prop = getattr(val, key)
                val = prop() if callable(prop) else prop
            else:
                val = None
                break
    
        return repr(val)
