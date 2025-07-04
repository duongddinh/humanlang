# HumanLang: The Complete Language Reference

**Version: 3.0.0**

Welcome to the official documentation for HumanLang, a high-level, object-oriented, and asynchronous programming language designed for ultimate readability and ease of use. This document provides a comprehensive reference for all syntax and features.

## Why? isn't this just python?

In simple terms yes but no, imagine Spanish is invented before English; it is like a person who trying to invent english but it is basically spanish. And for people to understand English, they have to translate English to Spanish.

## Core Philosophy: Just Talk to Your Code, Especially for Networks.

HumanLang is a "for fun" project, but it's built on a serious idea: **what if you could just *talk* to your computer and it understood your intentions, especially for complex tasks like networking?** Who wants to write complicated code anymore when you can simply describe what you want to do?

I believe code should be as easy to read as it is to write. By using a syntax that mirrors natural language, developers (and even non-developers\!) can focus purely on the logic of their applications, without getting bogged down in cryptic symbols, obscure libraries, or complex API calls.

**HumanLang is specifically designed to make networking operations intuitive and straightforward, removing the layers of abstraction usually required.** This means you can perform actions like port scans, send custom packets, or sniff network traffic using commands that sound like plain English, making network programming accessible and less error-prone.

## Getting Started

To run a HumanLang program, save your code in a file with a `.human` extension and execute it from your terminal:

```bash
humanlang your_script.human
```

**Note:** Many networking commands require administrative (`sudo`) privileges to run.

### Installation

```bash
git clone https://github.com/duongddinh/humanlang.git
cd humanlang
pip install -e .
```

-----

## **Part 1: Core Language Features**

### **1.1. Comments**

Comments are ignored by the interpreter and are used for documentation.

**Syntax:**
`# <Your comment here>`

**Example:**

```humanlang
# This line will be ignored by the interpreter.
```

### **1.2. Variables and Data Types**

Variables can be declared with an optional type for static analysis. If no type is declared, a variable is created upon its first assignment.

#### **Declaration and Assignment**

**Syntax:**

```humanlang
Declare <variable_name> as a <Type>.
Set <variable_name> to <value>.
```

**Supported Types:**

  * `String`: Textual data (e.g., `"Hello, World!"`).
  * `Number`: Integers or floating-point numbers (e.g., `42`, `3.14`).
  * `Boolean`: Represents `true` or `false`.
  * `List`: An ordered collection of items.
  * `Object`: A key-value collection, similar to a dictionary.
  * Custom class names (e.g., `MadScientist`).

**Example:**

```humanlang
Declare user_name as a String.
Set user_name to "Dr. Human".

Set score to 100. # Type is inferred as Number
```

### **1.3. Console Input and Output**

#### **Displaying Output**

Print values or expressions to the console.

**Syntax:**

```humanlang
print <expression>
show me <expression>
display <expression>
```

**Example:**

```humanlang
Set x to 10.
show me x. # Prints 10
print "The value of x is " + x. # Prints "The value of x is 10"
```

#### **User Input**

Prompt the user for input and store the result in a variable.

**Syntax:**
`Ask "<prompt_message>" and set the answer to <variable_name>.`

**Example:**

```humanlang
Ask "What is your name?" and set the answer to user_name.
```

### **1.4. Operators and Expressions**

#### **Mathematical Operations**

Perform basic arithmetic. The target of the operation must be a variable.

**Syntax:**

```humanlang
Add <value> to <variable>.
Subtract <value> from <variable>.
Multiply <variable> by <value>.
Divide <variable> by <value>.
```

**Example:**

```humanlang
Set score to 10.
Add 5 to score.      # score is now 15
Multiply score by 2. # score is now 30
show me score.       # Prints 30
```

#### **Comparison and Logical Operators**

Used in control flow statements like `if` and `while`.

  * **Comparison**: `is equal to`, `is not equal to`, `is greater than`, `is less than`
  * **Boolean**: `is true`, `is false`
  * **Logical**: `and`, `or`, `not`

**Example:**

```humanlang
If score is greater than 20 and player_is_active is true then
    print "You are winning!".
End if
```

### **1.5. Control Flow**

#### **If/Else Statement**

Execute code conditionally. The `Else` block is optional.

**Syntax:**

```humanlang
If <condition> then
    # Code to run if true
Else
    # Code to run if false
End if
```

#### **While Loop**

Repeat a block of code as long as a condition is true.

**Syntax:**

```humanlang
While <condition>
    # Loop body
End while
```

#### **For Loop**

Iterate over items in a list.

**Syntax:**
`For each <item_variable> in <list_variable>`

**Example:**

```humanlang
Declare names as a List.
# Note: List literals are not directly supported yet.
# Lists must be created by other means (e.g., from a file or function).
# For demonstration, assume 'names' is a list like ["Alice", "Bob"].
For each name in names
    print "Hello, " + name.
End for
```

-----

## **Part 2: Advanced Language Features**

### **2.1. Tasks (Functions)**

Tasks are reusable blocks of code that can accept parameters and return values.

**Syntax:**

```humanlang
Define a [asynchronous] task named "<task_name>"
    [that accepts "<param1>" of type <Type1>, "<param2>" of type <Type2>]
    [and returns a <ReturnType>].
    
    # Task body
    Return <value>
End task
```

**Performing a Task:**

```humanlang
# Synchronous call
Perform "<task_name>" with <arg1>, <arg2>.

# Store the result of a task
Perform "<task_name>" with <arg> and store the result in my_variable.
```

### **2.2. Concurrency**

HumanLang supports non-blocking, asynchronous operations, which are essential for I/O-bound tasks like network requests.

**Defining an Asynchronous Task:**

```humanlang
Define an asynchronous task named "fetch_website".
    Perform an http get request to "https://example.com" and store the result in html.
    print "Finished fetching website.".
End task
```

**Running Asynchronous Tasks:**

```humanlang
# Start the task in the background
Perform "fetch_website" asynchronously.
print "This message will appear immediately, without waiting for the fetch to finish.".

# Wait for all running async tasks to complete
Await all tasks.
print "Now all async tasks are done.".
```

### **2.3. Object-Oriented Programming**

Create custom data structures using classes, properties, and methods.

**Class Definition:**

```humanlang
Define a class named "<ClassName>" [that inherits from "<ParentClass>"].
    It has a property named "<prop_name>" of type <Type>.
    
    # The initializer is a special method called when a new instance is created.
    Define a task named "initializer" that accepts ...
        Set this's <prop_name> to ...
    End task

    # Other methods
    Define a task named "<method_name>" ...
    End task
End class
```

**Instantiation and Usage:**

```humanlang
# Create an object from a class
Create a new "<ClassName>" [with <arg1>] and call it <variable_name>.

# Access properties and methods
print <variable_name>'s <prop_name>.
Perform <variable_name>'s task named "<method_name>".
```

### **2.4. Error Handling**

Gracefully manage runtime errors without crashing the program.

**Syntax:**

```humanlang
Try to
    # Code that might fail
On error
    # This code runs only if the 'Try to' block fails.
    # The error details are automatically stored in the 'error_message' variable.
    print "An error occurred: " + error_message.
End try
```

### **2.5. Modules**

Split your code into multiple files for better organization.

**Syntax:**
`use the library "<relative/path/to/your/file.human>"`

-----

## **Part 3: I/O and Data Handling**

### **3.1. File I/O**

Read from and write to files on the local system.

**Write to File:**
`Write <expression> to the file <filename_expression>.`

**Read from File:**
`Read the file "<filename>" and store the contents in <variable>.`

**Example:**

```humanlang
Set my_data to "This is a test.".
Set my_filename to "report.txt".
Write my_data to the file my_filename.

Read the file "report.txt" and store the contents in file_content.
print file_content.
```

### **3.2. Web APIs and JSON**

Fetch data from web APIs and parse JSON responses.

**HTTP GET Request:**
`Perform an http get request to <url_expression> and store the result in <variable>.`

**JSON Parsing:**
`Parse the json string <json_variable> and store the result in <variable>.`

**Example:**

```humanlang
Declare api_url as a String.
Set api_url to "https://official-joke-api.appspot.com/random_joke".

Perform an http get request to api_url and store the result in joke_json.
Parse the json string joke_json and store the result in joke_data.

print "Setup: " + joke_data's setup.
print "Punchline: " + joke_data's punchline.
```

-----

## **Part 4: Networking & Security Toolkit**

**This is where HumanLang truly shines\!** We've integrated powerful networking capabilities directly into the language with intuitive, human-readable commands. Forget complex library imports and obscure function calls – just tell HumanLang what you want to do.

**Note:** These commands often require administrative (`sudo`) privileges.

### **4.1. Network Diagnostics: Just Ask HumanLang to Check the Network.**

  * **ARP Scan**: Discover live hosts on a local network.
      * `Perform an arp scan on <network_cidr> and store the results in <variable>.`
  * **Ping**: Test host reachability.
      * `Perform a ping to <host> and store the result in <variable>.`
  * **Traceroute**: Map the path to a host.
      * `Perform a traceroute to <host> and store the result in <variable>.`

### **4.2. Port Scanning: Find Open Doors on a Target.**

  * **TCP SYN Scan**: Quickly check for open TCP ports.
      * `Perform a port scan on <host> for ports "<ports>" and store the results in <variable>.`
          * `<ports>` can be a comma-separated list (e.g., `"22,80,443"`) or a range (e.g., `"20-1024"`).

### **4.3. Packet Crafting & Sending: Build and Blast Custom Packets.**

No more deep dives into packet structures. HumanLang lets you describe your packets layer by layer and send them.

1.  **Create Packet**: Define your packet's layers.
      * `Create a new "Packet" with layers "<Layer1/Layer2>" and call it <packet_variable>.`
          * Supported layers: `ETHER`, `IP`, `TCP`, `ICMP`, `ARP`.
2.  **Configure Packet**: Set specific fields as you would any variable.
      * `Set <packet_variable>'s <property> to <value>.`
          * Common properties include: `dst` (destination), `dport` (destination port), `flags` (`"S"` for SYN, `"A"` for ACK, etc.), `src`, `sport`.
3.  **Send Packet**: Launch your crafted packet and capture the reply.
      * `Send packet <packet_variable> and store the reply in <reply_variable>.`

### **4.4. Network Sniffing: Listen to the Network Conversation.**

  * **Capture Traffic**: Intercept and analyze packets flowing through an interface.
      * `Start sniffing on interface "<iface>" with filter "<bpf_filter>" for <seconds> seconds and store packets in <variable>.`
