#!/usr/bin/env python3
"""
Simple command-line calculator supporting basic arithmetic operations.
"""

def calculate(num1, operator, num2):
    """Perform calculation based on operator."""
    if operator == '+':
        return num1 + num2
    elif operator == '-':
        return num1 - num2
    elif operator == '*':
        return num1 * num2
    elif operator == '/':
        if num2 == 0:
            raise ValueError("Cannot divide by zero")
        return num1 / num2
    else:
        raise ValueError(f"Invalid operator: {operator}")

def main():
    """Main calculator loop."""
    print("Simple Calculator")
    print("Enter calculations in format: number operator number")
    print("Supported operators: + - * /")
    print("Type 'q' to quit\n")
    
    while True:
        try:
            user_input = input(">>> ").strip()
            
            if user_input.lower() == 'q':
                print("Goodbye!")
                break
            
            parts = user_input.split()
            if len(parts) != 3:
                print("Error: Please enter in format: number operator number")
                continue
            
            num1 = float(parts[0])
            operator = parts[1]
            num2 = float(parts[2])
            
            result = calculate(num1, operator, num2)
            print(f"Result: {result}\n")
            
        except ValueError as e:
            print(f"Error: {e}\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}\n")

if __name__ == "__main__":
    main()
