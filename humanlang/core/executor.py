import re
import json
import sys
import asyncio
import aiohttp
from scapy.all import srp, Ether, ARP, sr1, IP, TCP, ICMP, sr, traceroute, sniff
from .structures import Environment, ObjectInstance, ReturnValue

class Executor:
    def __init__(self, interpreter):
        self.interpreter = interpreter

    async def execute(self, blocks, env):
        # This allows the handle_try function to correctly manage errors
        for stmt in blocks:
            try:
                if isinstance(stmt, list):
                    head = stmt[0].lower().strip()
                    if head.startswith('try to'):
                        await self.handle_try(stmt, env)
                    elif not head.startswith(('define a class', 'define a task')):
                        await self.eval_block(stmt, env)
                elif isinstance(stmt, str) and not stmt.lower().startswith('use the library'):
                    await self.eval_line(stmt, env)
            except ReturnValue:
                raise

    async def eval_block(self, block, env):
        head = block[0].lower().strip()
        if head.startswith('if'):
            await self.handle_if(block, env)
        elif head.startswith('for each'):
            await self.handle_for(block, env)
        elif head.startswith('while'):
            await self.handle_while(block, env)

    async def eval_line(self, line, env):
        line = line.strip()
        if not line or line.startswith('#'):
            return

        commands = {
            "declare": self.handle_declare, "set ": self.handle_set,
            "create a new ": self.handle_create_instance, "add ": self.handle_math,
            "subtract ": self.handle_math, "multiply ": self.handle_math,
            "divide ": self.handle_math, "ask ": self.handle_input,
            "perform an arp scan on": self.handle_arp_scan,
            "perform a port scan on": self.handle_port_scan,
            "perform a ping to": self.handle_ping,
            "perform a traceroute to": self.handle_traceroute,
            "send packet": self.handle_send_packet,
            "start sniffing": self.handle_sniff,
            "perform ": self.handle_perform, "await all tasks": self.handle_await_all,
            "parse the json string": self.handle_parse_json, "return ": self.handle_return,
            "show me ": self.handle_print, "print ": self.handle_print,
            "display ": self.handle_print, "write ": self.handle_file_write,
            "read the file": self.handle_file_read
        }

        for cmd, handler in commands.items():
            if line.lower().startswith(cmd):
                if asyncio.iscoroutinefunction(handler):
                    if cmd in ["add ", "subtract", "multiply ", "divide "]:
                        await handler(line, cmd.strip(), env)
                    else:
                        await handler(line, env)
                else:
                    handler(line, env)
                return
        raise ValueError(f"I don't understand the command: '{line}'")

    def handle_declare(self, line, env):
        pass

    def handle_input(self, line, env):
        match = re.match(r'ask "(.+)" and set the answer to (\w+)', line, re.I)
        if match:
            prompt, var_name = match.groups()
            env.set(var_name, input(prompt + " "))

    def handle_file_read(self, line, env):
        match = re.match(r'read the file "([^"]+)" and store the contents in (\w+)', line, re.I)
        filepath, var_name = match.groups()
        with open(filepath, 'r') as f:
            env.set(var_name, f.read())

    async def handle_try(self, block, env):
        body = block[1:]
        on_error_index = -1

        # Correctly find the index by iterating through the original 'body' list
        for i, stmt in enumerate(body):
            if isinstance(stmt, str) and stmt.strip().lower() == 'on error':
                on_error_index = i
                break

        # If 'on error' was not found, raise an error
        if on_error_index == -1:
            raise SyntaxError("A 'Try to' block must have a matching 'On error' part.")

        # Slice the body correctly using the proper index
        try_body = body[:on_error_index]
        error_body = body[on_error_index + 1:]

        try:
            await self.execute(try_body, env)
        except Exception as e:
            error_env = Environment(outer=env)
            error_env.set("error_message", str(e), "String")
            await self.execute(error_body, error_env)

    async def handle_set(self, line, env):
        packet_prop_match = re.match(r"set (.+)'s (\w+) to (.+)", line, re.I)
        var_match = re.match(r'set (\w+) to (.+)', line, re.I)

        if packet_prop_match:
            obj_name, prop, expr = packet_prop_match.groups()
            instance = env.get(obj_name)
            
            clean_expr_match = re.match(r"(.*?)(?:\s*#.*)?$", expr)
            clean_expr = clean_expr_match.group(1).strip()
            
            value = await self.interpreter.eval_expr(clean_expr, env)
            
            if hasattr(instance, 'haslayer') and hasattr(instance, 'getlayer'):
                if prop in ['dport', 'sport', 'flags', 'seq', 'ack'] and instance.haslayer(TCP):
                    setattr(instance.getlayer(TCP), prop, value)
                elif prop in ['dst', 'src', 'ttl', 'id'] and instance.haslayer(IP):
                    setattr(instance.getlayer(IP), prop, value)
                elif prop in ['dst', 'src'] and instance.haslayer(Ether):
                    setattr(instance.getlayer(Ether), prop, value)
                else:
                    setattr(instance, prop, value)
            elif isinstance(instance, ObjectInstance):
                 instance.env.set(prop, value)
            else:
                env.set(obj_name, value)

        elif var_match:
            var, expr = var_match.groups()
            value = await self.interpreter.eval_expr(expr.strip(), env)
            # If it doesn't exist, set it in the current scope.
            if not env.update(var, value):
                env.set(var, value)
        else:
            raise SyntaxError(f"Invalid 'set' command: {line}")

    async def handle_create_instance(self, line, env):
        packet_match = re.match(r'create a new "Packet" with layers "(.+)" and call it (\w+)', line, re.I)
        class_match = re.match(r'create a new "([^"]+)"(?: with (.+))? and call it (\w+)', line, re.I)

        if packet_match:
            layers_str, var_name = packet_match.groups()
            layers = [l.strip().upper() for l in layers_str.split('/')]
            
            packet_structure = None
            layer_map = {"ETHER": Ether, "IP": IP, "TCP": TCP, "ICMP": ICMP, "ARP": ARP}
            for layer_name in layers:
                if layer_name not in layer_map:
                    raise ValueError(f"Unknown packet layer: {layer_name}")
                if packet_structure is None:
                    packet_structure = layer_map[layer_name]()
                else:
                    packet_structure /= layer_map[layer_name]()
            
            env.set(var_name, packet_structure)

        elif class_match:
            class_name, args_str, var_name = class_match.groups()
            class_def = self.interpreter.classes.get(class_name)
            instance = ObjectInstance(class_def)
            env.set(var_name, instance, class_name)
            if class_def.find_method("initializer"):
                await self.interpreter._call_method(instance, "initializer", args_str, env)
        else:
            raise SyntaxError(f"Invalid 'create a new' command: {line}")

    async def handle_if(self, block, env):
        condition_str = re.match(r'if (.+) then', block[0], re.I).group(1)
        body = block[1:]
        try:
            else_index = [s.strip().lower() for s in body if isinstance(s, str)].index('else')
            if_body, else_body = body[:else_index], body[else_index + 1:]
        except ValueError:
            if_body, else_body = body, None
        if await self.interpreter.eval_expr(condition_str, env):
            await self.execute(if_body, env)
        elif else_body:
            await self.execute(else_body, env)

    async def handle_while(self, block, env):
        condition_str = re.match(r'while (.+) is true', block[0], re.I).group(1)
        body = block[1:]
        while await self.interpreter.eval_expr(condition_str, env):
            await self.execute(body, env)

    async def handle_for(self, block, env):
        match = re.match(r'for each (\w+) in (\w+)', block[0], re.I)
        item_var, list_var_name = match.groups()
        the_list = env.get(list_var_name)
        if not isinstance(the_list, list): raise TypeError(f"'{list_var_name}' is not a list.")
        body = block[1:]
        for item in the_list:
            loop_env = Environment(outer=env)
            loop_env.set(item_var, item)
            await self.execute(body, loop_env)

    async def handle_perform(self, line, env):
        http_match = re.match(r'perform an http get request to (.+?) and store the result in (\w+)', line, re.I)
        async_match = re.match(r'perform "([^"]+)"(?: with (.+))? asynchronously', line, re.I)
        method_match = re.match(r"perform (\w+)'s task named \"([^\"]+)\"(?: with (.+))?(?: and store the result in (\w+))?", line, re.I)
        task_match = re.match(r'perform "([^"]+)"(?: with (.+))?(?: and store the result in (\w+))?', line, re.I)
        
        if http_match:
            url_expr, var_name = http_match.groups()
            url = await self.interpreter.eval_expr(url_expr, env)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if not response.ok: raise IOError(f"HTTP request failed with status {response.status}")
                    result = await response.text()
                    env.set(var_name, result, "String")
        elif async_match:
            task_name, args_str = async_match.groups()
            task_def = self.interpreter.global_tasks.get(task_name)
            if not task_def or not task_def.get('is_async'):
                raise TypeError(f"Task '{task_name}' is not defined as an asynchronous task.")
            coro = self.interpreter._call_task_or_method(task_def, args_str, env, None)
            task = asyncio.create_task(coro)
            if not env.get("running_tasks"): env.set("running_tasks", [])
            env.get("running_tasks").append(task)
        elif method_match:
            obj_name, method_name, args_str, result_var = method_match.groups()
            instance = env.get(obj_name)
            result = await self.interpreter._call_method(instance, method_name, args_str, env)
            if result_var: env.set(result_var, result)
        elif task_match:
            task_name, args_str, result_var = task_match.groups()
            task = self.interpreter.global_tasks.get(task_name)
            if not task: raise NameError(f"Global task '{task_name}' is not defined.")
            result = await self.interpreter._call_task_or_method(task, args_str, self.interpreter.global_env, self.interpreter.global_env)
            if result_var: env.set(result_var, result)

    async def handle_await_all(self, line, env):
        tasks = env.get("running_tasks")
        if tasks and len(tasks) > 0:
            await asyncio.gather(*tasks)
            env.set("running_tasks", [])

    async def handle_parse_json(self, line, env):
        match = re.match(r'parse the json string (.+?) and store the result in (\w+)', line, re.I)
        json_expr, var_name = match.groups()
        json_string = await self.interpreter.eval_expr(json_expr, env)
        data = json.loads(json_string)
        env.set(var_name, data, "Object")

    async def handle_return(self, line, env):
        expr = line.split(" ", 1)[1]
        value = await self.interpreter.eval_expr(expr, env)
        raise ReturnValue(value)

    async def handle_print(self, line, env):
        expr = re.search(r'(?:show me|print|display)\s+(.+)', line, re.I).group(1)
        value = await self.interpreter.eval_expr(expr, env)
        if hasattr(value, 'summary'):
            print(value.summary())
        else:
            print(value)

    async def handle_math(self, line, op, env):
        patterns = {
            'add': r'add (.+) to (.+)', 'subtract': r'subtract (.+) from (.+)',
            'multiply': r'multiply (.+) by (.+)', 'divide': r'divide (.+) by (.+)'
        }
        match = re.match(patterns[op], line, re.I)
        if not match: raise SyntaxError(f"Invalid math operation: {line}")

        str1, str2 = match.groups()
        if op in ['add', 'subtract']:
            val_expr, target_expr = str1, str2
        else:
            target_expr, val_expr = str1, str2
        
        val = await self.interpreter.eval_expr(val_expr, env)
        target_val = await self.interpreter.eval_expr(target_expr, env)
        ops = {'add': target_val + val, 'subtract': target_val - val,
               'multiply': target_val * val, 'divide': target_val / val}
        set_command = f"set {target_expr} to {ops[op]}"
        await self.handle_set(set_command, env)

    async def handle_file_write(self, line, env):
        match = re.match(r'write (.+) to the file (.+)', line, re.I)
        if not match:
             raise SyntaxError(f"Invalid file write syntax: {line}")
        expr, filepath_expr = match.groups()
        content = await self.interpreter.eval_expr(expr, env)
        filepath = await self.interpreter.eval_expr(filepath_expr, env)
        with open(filepath, 'w') as f: f.write(str(content))

    async def handle_arp_scan(self, line, env):
        match = re.match(r'perform an arp scan on (.+?) and store the results in (\w+)', line, re.I)
        network_expr, var_name = match.groups()
        network_cidr = await self.interpreter.eval_expr(network_expr, env)
        print(f"Starting ARP scan on {network_cidr}... (This may require root privileges)")
        try:
            ans, _ = await asyncio.to_thread(srp, Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=network_cidr), timeout=3, verbose=False)
        except PermissionError: raise PermissionError("ARP scans require root/administrator privileges.")
        results = [{'ip': r.psrc, 'mac': r.hwsrc} for s, r in ans]
        env.set(var_name, results, "List of Object")
        print(f"ARP scan complete. Found {len(results)} hosts.")

    async def handle_ping(self, line, env):
        match = re.match(r'perform a ping to (.+?) and store the result in (\w+)', line, re.I)
        if not match: raise SyntaxError("Invalid ping command syntax.")
        
        host_expr, var_name = match.groups()
        host = await self.interpreter.eval_expr(host_expr, env)
        print(f"Pinging {host}... (This may require root privileges)")
        
        try:
            ans, unans = await asyncio.to_thread(sr, IP(dst=host)/ICMP(), timeout=4, verbose=False)
            summary = ""
            if ans:
                summary += f"Received {len(ans)} packets from {host}:\n"
                for sent, received in ans:
                    summary += f"  - Reply from {received.src}: time={(received.time - sent.sent_time)*1000:.2f}ms\n"
            if unans:
                summary += f"Lost {len(unans)} packets.\n"
            
            env.set(var_name, summary.strip(), "String")
            print("Ping complete.")
        except PermissionError:
            raise PermissionError("Ping operations require root/administrator privileges.")
        except Exception as e:
            env.set(var_name, f"Ping failed: {e}", "String")
            print(f"Ping failed: {e}")

    async def handle_traceroute(self, line, env):
        match = re.match(r'perform a traceroute to (.+?) and store the result in (\w+)', line, re.I)
        if not match: raise SyntaxError("Invalid traceroute command syntax.")

        host_expr, var_name = match.groups()
        host = await self.interpreter.eval_expr(host_expr, env)
        print(f"Performing traceroute to {host}... (This may require root privileges)")

        try:
            results, _ = await asyncio.to_thread(traceroute, host, verbose=False)
            output = f"Traceroute to {host}:\n"
            output += "Hop\tRTT (ms)\tAddress\n"
            output += "---------------------------------------\n"
            
            trace = results.get_trace()
            for dest, hops in trace.items():
                for ttl, (ip, rtt) in sorted(hops.items()):
                    output += f"{ttl}\t{rtt*1000:<15.2f}\t{ip}\n"

            env.set(var_name, output, "String")
            print("Traceroute complete.")
        except PermissionError:
            raise PermissionError("Traceroute operations require root/administrator privileges.")
        except Exception as e:
            env.set(var_name, f"Traceroute failed: {e}", "String")
            print(f"Traceroute failed: {e}")

    async def handle_port_scan(self, line, env):
        match = re.match(r'perform a port scan on (.+?) for ports (.+?) and store the results in (\w+)', line, re.I)
        if not match: raise SyntaxError("Invalid port scan command.")

        host_expr, ports_expr, var_name = match.groups()
        host = await self.interpreter.eval_expr(host_expr, env)
        ports_str = await self.interpreter.eval_expr(ports_expr, env)
        
        if '-' in ports_str:
            start, end = map(int, ports_str.split('-'))
            ports = range(start, end + 1)
        else:
            ports = [int(p.strip()) for p in ports_str.split(',')]

        print(f"Scanning {host} for ports {ports_str}... (This may require root privileges)")
        
        ans, unans = await asyncio.to_thread(sr, IP(dst=host)/TCP(dport=ports, flags="S"), timeout=5, verbose=False)
        
        results = {}
        for sent, received in ans:
            port = sent[TCP].dport
            flag = received[TCP].flags
            if flag == 0x12:
                results[port] = "Open"
            elif flag == 0x14:
                results[port] = "Closed"
        
        for sent in unans:
            results[sent[TCP].dport] = "Filtered"

        env.set(var_name, results, "Object")
        print("Port scan complete.")


    async def handle_send_packet(self, line, env):
        match = re.match(r'send packet (.+?) and store the reply in (\w+)', line, re.I)
        if not match:
            raise SyntaxError("Invalid send packet command.")

        packet_expr_str, reply_var = match.groups()
        
        # Evaluate the packet expression to get the actual packet object
        packet_to_send = await self.interpreter.eval_expr(packet_expr_str.strip(), env) # Use eval_expr here
        
        # Dynamically determine the destination for printing based on available layers
        destination_info = "unknown destination"
        if hasattr(packet_to_send, 'haslayer'): # Ensure it's a Scapy packet before checking layers
            if packet_to_send.haslayer(IP):
                destination_info = packet_to_send[IP].dst
            elif packet_to_send.haslayer(ARP):
                destination_info = packet_to_send[ARP].pdst
            else:
                # If no IP/ARP layer, fallback to summary or convert to string
                destination_info = packet_to_send.summary() 
        else:
            destination_info = self._to_display_string(packet_to_send) # Convert to display string

        print(f"Sending custom packet to {destination_info}...")
        
        if hasattr(packet_to_send, 'summary'):
            print(f"Packet details: {packet_to_send.summary()}")
        else:
            print(f"Packet details: {self._to_display_string(packet_to_send)}") # Use helper for non-Scapy objects
        
        try:
            ans, unans = await asyncio.to_thread(sr, packet_to_send, timeout=3, verbose=False)
            if ans:
                env.set(reply_var, ans[0][1])
                print(f"Reply details: {ans[0][1].summary()}")
            else:
                env.set(reply_var, None)
                print("No reply received.")
            print("Packet sent.")
        except PermissionError:
            raise PermissionError("Sending custom packets requires root/administrator privileges.")
            
    async def handle_sniff(self, line, env):
        match = re.match(r'start sniffing on interface (.+?) with filter "(.+?)" for (\d+) seconds and store packets in (\w+)', line, re.I)
        if not match: raise SyntaxError("Invalid sniff command.")

        iface_expr, filter_expr, duration_str, var_name = match.groups()
        
        iface = await self.interpreter.eval_expr(iface_expr, env)
        bpf_filter = filter_expr
        duration = int(duration_str)

        print(f"Starting packet sniff on {iface} for {duration} seconds with filter '{bpf_filter}'...")
        try:
            packets = await asyncio.to_thread(sniff, iface=iface, filter=bpf_filter, timeout=duration)
            packet_summaries = [p.summary() for p in packets]
            env.set(var_name, packet_summaries)
            print(f"Sniffing complete. Captured {len(packets)} packets.")
        except PermissionError:
            raise PermissionError("Sniffing requires root/administrator privileges.")
