import json
import os
import re

# ===== ALPHABET =====
ALPHABET = (
    "0123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    " .,!?:;–()[]{}+-=*%^√&#@|/\\_`'°∆$~"
)
N = len(ALPHABET)
ALPHA_INDEX = {c: i for i, c in enumerate(ALPHABET)}

# ===== PROTOCOLS FILE =====
PROTOCOLS_FILE = "protocols.json"

def load_protocols():
    if not os.path.exists(PROTOCOLS_FILE):
        return {}
    
    try:
        with open(PROTOCOLS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        print("\n" + "*"*35)
        print("⚠️ Invalid protocols.json file format")
        print("The file contains corrupted data.")
        print("1 – delete file and create new one")
        print("0 – exit program")
        choice = input("> ").strip()
        if choice == "1":
            os.remove(PROTOCOLS_FILE)
            return {}
        else:
            exit(0)
    
    if not isinstance(data, dict):
        print("\n" + "*"*35)
        print("⚠️ Invalid protocols.json file format")
        print("Expected dictionary, got", type(data).__name__)
        print("1 – delete file and create new one")
        print("0 – exit program")
        choice = input("> ").strip()
        if choice == "1":
            os.remove(PROTOCOLS_FILE)
            return {}
        else:
            exit(0)
    
    corrupted = []
    valid = {}
    for name, proto in data.items():
        if not isinstance(name, str) or not isinstance(proto, str):
            corrupted.append(f"{name}: {proto}")
        else:
            valid[name] = proto
    
    if corrupted:
        print("\n" + "*"*35)
        print("⚠️ Corrupted entries found in protocols.json:")
        for item in corrupted:
            print(f"  {item}")
        print("\n1 – delete corrupted entries")
        print("2 – leave as is (errors may occur)")
        print("0 – exit program")
        choice = input("> ").strip()
        if choice == "1":
            save_protocols(valid)
            return valid
        elif choice == "0":
            exit(0)
    
    return data

def save_protocols(protocols):
    with open(PROTOCOLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(protocols, f, indent=2, ensure_ascii=False)

# ===== MAIN FUNCTIONS =====
def apply_shift(text, shift):
    result = []
    for c in text:
        if c not in ALPHA_INDEX:
            raise ValueError(f"Invalid character: {c}")
        new_idx = (ALPHA_INDEX[c] + shift) % N
        result.append(ALPHABET[new_idx])
    return "".join(result)

def apply_mirror(text, block_size):
    if block_size <= 0:
        raise ValueError("Block size must be positive")
    result = []
    for i in range(0, len(text), block_size):
        result.append(text[i:i + block_size][::-1])
    return "".join(result)

def apply_linear_with_mode(text, k_str, mode="encrypt"):
    if k_str.startswith('*'):
        k_str = '0.' + k_str[1:]
    elif k_str.startswith('-*'):
        k_str = '-0.' + k_str[2:]
    try:
        K = float(k_str)
    except ValueError:
        raise ValueError(f"Invalid coefficient for linear function: {k_str}")
    result = []
    for i, c in enumerate(text):
        if c not in ALPHA_INDEX:
            raise ValueError(f"Invalid character: {c}")
        raw_shift = K * (i + 1)
        shift = int(round(raw_shift))
        if mode == "decrypt":
            shift = -shift
        new_idx = (ALPHA_INDEX[c] + shift) % N
        result.append(ALPHABET[new_idx])
    return "".join(result)

def apply_wave(text, height, mode="encrypt"):
    """Wave function with proper reversibility"""
    if height == 0:
        return text
    
    H = abs(height)
    
    # Base sequence for positive height
    base_inc = []
    for i in range(H, 0, -1):
        base_inc.append(i)
    for i in range(1, H + 1):
        base_inc.append(-i)
    
    # Full sequence for positive wave
    pos_inc = base_inc + [-x for x in base_inc]
    
    # Determine sequence based on mode and sign
    if mode == "decrypt":
        increments = [-x for x in pos_inc]
    else:
        increments = pos_inc
    
    # If original height is negative — invert
    if height < 0:
        increments = [-x for x in increments]
    
    result = []
    current = 0
    for i, c in enumerate(text):
        if c not in ALPHA_INDEX:
            raise ValueError(f"Invalid character: {c}")
        new_idx = (ALPHA_INDEX[c] + current) % N
        result.append(ALPHABET[new_idx])
        current += increments[i % len(increments)]
    
    return "".join(result)

# ===== INTEGER CHECK =====
def is_integer(s):
    s = s.strip()
    if s.startswith('-'):
        s = s[1:]
    return s.isdigit()

# ===== PROTOCOL PROCESSING =====
def process_protocol(protocol, text, mode):
    commands = []
    i = 0
    while i < len(protocol):
        cmd = protocol[i]
        if cmd not in ('p', 'm', 'l', 'w'):
            raise ValueError(f"❌ Unknown command: {cmd}")
        i += 1
        
        param = ""
        while i < len(protocol) and protocol[i] not in ('p', 'm', 'l', 'w'):
            param += protocol[i]
            i += 1
        
        if not param:
            raise ValueError(f"❌ No parameter for command {cmd}")
        
        commands.append((cmd, param))
    
    if mode == "decrypt":
        commands = commands[::-1]
    
    for cmd, param in commands:
        if cmd == 'p':
            if not is_integer(param):
                raise ValueError(f"❌ Command p must contain an integer (got: {param})")
            shift = int(param)
            if mode == "decrypt":
                shift = -shift
            text = apply_shift(text, shift)
        elif cmd == 'm':
            if not is_integer(param):
                raise ValueError(f"❌ Command m must contain an integer (got: {param})")
            text = apply_mirror(text, int(param))
        elif cmd == 'l':
            text = apply_linear_with_mode(text, param, mode)
        elif cmd == 'w':
            if not is_integer(param):
                raise ValueError(f"❌ Command w must contain an integer (got: {param})")
            height = int(param)
            text = apply_wave(text, height, mode)
    
    return text

# ===== PROTOCOL VERIFICATION =====
def check_protocol(protocol, original_text):
    try:
        encrypted = process_protocol(protocol, original_text, "encrypt")
        decrypted = process_protocol(protocol, encrypted, "decrypt")
        return (decrypted == original_text), encrypted, decrypted
    except Exception as e:
        return False, None, str(e)

# ===== COMMAND PARSING =====
def parse_command(data, protocols):
    data = data.strip()
    if data.startswith('#'):
        parts = data[1:].split('/', 1)
        if len(parts) != 2:
            return None, None, "Use format: #name/text"
        name, text = parts
        if name not in protocols:
            return None, None, f"❌ Protocol \"{name}\" not found."
        return protocols[name], text, None
    else:
        if '/' not in data:
            return None, None, "Error: use format protocol/text"
        protocol, text = data.split('/', 1)
        return protocol, text, None

# ===== PROTOCOL MANAGEMENT =====
def show_protocols_list(protocols):
    if not protocols:
        print("\nYou have no saved protocols.\n")
        return False
    items = list(protocols.items())
    print("\nYour protocols:")
    for idx, (name, proto) in enumerate(items, 1):
        print(f"{idx}. {name}/{proto}")
    print()
    return True

def add_protocol(protocols):
    while True:
        entry = input("Enter template in format name/protocol: ").strip()
        if entry.count('/') != 1:
            print("🚫 Invalid format! Must contain exactly one / symbol")
            print("Example: D3@f7/p37l0.7m3l*3")
            continue
        
        name, proto = entry.split('/', 1)
        
        if not name:
            print("🚫 Name cannot be empty.")
            continue
        
        if not proto:
            print("🚫 Protocol cannot be empty.")
            continue
        
        if name in protocols:
            print(f"⚠️ Protocol with name \"{name}\" already exists.")
            print("1 – replace existing")
            print("2 – enter different name")
            print("0 – cancel")
            choice = input("> ").strip()
            if choice == "1":
                protocols[name] = proto
                save_protocols(protocols)
                print(f"✅ Saved as \"{name}\"")
                print("//////////////////////////////////////////////////")
                return
            elif choice == "2":
                continue
            else:
                return
        else:
            protocols[name] = proto
            save_protocols(protocols)
            print(f"✅ Saved as \"{name}\"")
            print("//////////////////////////////////////////////////")
            return

def edit_protocol(protocols):
    if not show_protocols_list(protocols):
        return
    items = list(protocols.items())
    choice = input("Enter protocol number to edit: ").strip()
    if not choice.isdigit():
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(items):
        return
    old_name, old_proto = items[idx]
    print(f"Editing: {old_name}/{old_proto}")
    
    entry = input("Enter new template name/protocol: ").strip()
    if entry.count('/') != 1:
        print("🚫 Invalid format! Must contain exactly one / symbol")
        return
    
    name, proto = entry.split('/', 1)
    
    if not name:
        print("🚫 Name cannot be empty.")
        return
    
    if not proto:
        print("🚫 Protocol cannot be empty.")
        return
    
    if name != old_name and name in protocols:
        print(f"⚠️ Protocol with name \"{name}\" already exists.")
        print("1 – replace existing")
        print("2 – enter different name")
        print("0 – cancel")
        subchoice = input("> ").strip()
        if subchoice == "1":
            protocols[name] = proto
            if name != old_name:
                del protocols[old_name]
            save_protocols(protocols)
            print("✅ Protocol updated.")
            print("//////////////////////////////////////////////////")
        return
    
    protocols[name] = proto
    if name != old_name:
        del protocols[old_name]
    save_protocols(protocols)
    print("✅ Protocol updated.")
    print("//////////////////////////////////////////////////")

def delete_protocols(protocols):
    if not show_protocols_list(protocols):
        return
    choice = input("Enter protocol number(s) (space separated) (! – delete all, 0 – back): ").strip()
    if choice == "0":
        return
    items = list(protocols.items())
    if choice == "!":
        print("Are you sure you want to delete ALL protocols?")
        print("1 – delete")
        print("0 – go back")
        if input("> ").strip() == "1":
            protocols.clear()
            save_protocols(protocols)
            print("✅ Protocols successfully deleted.")
            print("//////////////////////////////////////////////////")
        return
    indices = []
    names_to_delete = []
    display_names = []
    for part in choice.split():
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(items):
                indices.append(idx)
                name, proto = items[idx]
                names_to_delete.append(name)
                display_names.append(f"{name}/{proto}")
    if not names_to_delete:
        return
    print(f"Are you sure you want to delete the following templates: {'; '.join(display_names)}?")
    print("1 – delete")
    print("0 – go back")
    if input("> ").strip() == "1":
        for name in names_to_delete:
            if name in protocols:
                del protocols[name]
        save_protocols(protocols)
        print("✅ Protocols successfully deleted.")
        print("//////////////////////////////////////////////////")

def protocols_menu(protocols):
    while True:
        if protocols:
            show_protocols_list(protocols)
            print("1 – add protocol")
            print("2 – edit protocol")
            print("3 – delete protocols")
            print("4 – copy protocol")
            print("0 – back")
        else:
            print("You have no saved protocols.\n")
            print("1 – add protocol")
            print("0 – back")
        choice = input("> ").strip()
        if choice == "0":
            break
        elif choice == "1":
            add_protocol(protocols)
        elif choice == "2":
            edit_protocol(protocols)
        elif choice == "3":
            delete_protocols(protocols)
        elif choice == "4":
            print("⏳ This feature will be available later.")
        else:
            print("Unknown command.")

# ===== INSTRUCTION =====
def show_instruction():
    print("\n" + "="*35)
    print("PROTOCOL USAGE INSTRUCTION")
    print("="*35)
    print("\nA protocol is a key for encrypting and decrypting messages,")
    print("using combinations of the functions shown below.")
    print("\n" + "-"*35)
    print("PROTOCOL FORMAT:")
    print("-"*35)
    print("  [function1][parameter][function2][parameter]... / text")
    print("\n  Parameters are placed right after the function without spaces.")
    print("  Functions are applied sequentially from left to right.")
    print("\n" + "-"*35)
    print("AVAILABLE FUNCTIONS:")
    print("-"*35)
    print("  pN   – shift by N positions in alphabet")
    print("         N – integer (can be negative)")
    print("  mN   – mirror reflection of blocks of size N")
    print("         N – positive integer")
    print("  lK   – shift change by linear function")
    print("         K – integer or decimal (*5 = 0.5)")
    print("  wA   – wave shift changing from -A to A")
    print("         A – integer (positive or negative)")
    print("\n" + "-"*35)
    print("PROTOCOL EXAMPLES:")
    print("-"*35)
    print("  p3m2/12345")
    print("  l*5p2/hello")
    print("  w3p2/Привет")
    print("  m5w-2/Test")
    print("\n" + "-"*35)
    print("USING SAVED PROTOCOLS:")
    print("-"*35)
    print("  #name/text – apply saved protocol")
    print("  Example: #base32/Hello")
    print("\n  Save a protocol in menu 4.")
    print("\n" + "="*35)
    input("Press Enter to continue...")

# ===== MAIN LOOP =====
def main():
    protocols = load_protocols()
    while True:
        print("\n" + "="*40)
        print("CUSTOM CYPHER PROTOCOL SYSTEM (CCPS)")
        print("V1.0")
        print("Security is not given. It is constructed.")
        print("Build Your Own Cypher.")
        print("="*40)
        print("Powered by Dendr0_0")
        print("="*40)
        print("1 – encrypt")
        print("2 – decrypt")
        print("3 – verify function")
        print("4 – manage saved protocols")
        print("0 – exit")
        choice = input("> ").strip()
        if choice == "0":
            break
        elif choice == "4":
            protocols_menu(protocols)
            continue
        elif choice not in ("1", "2", "3"):
            print("Unknown command.")
            continue
        while True:
            data = input("Enter command (i – instruction, 0 – main menu): ").strip()
            if data == "0":
                break
            if data.lower() == "i":
                show_instruction()
                continue
            protocol, text, error = parse_command(data, protocols)
            if error:
                print(error)
                continue
            try:
                if choice == "3":
                    is_ok, encrypted, decrypted = check_protocol(protocol, text)
                    if encrypted is None:
                        print(f"\n{protocol}/{decrypted}")
                        print("⚠️PROTOCOL ERROR!⚠️")
                    else:
                        print()
                        i = 0
                        parts = []
                        while i < len(protocol):
                            cmd = protocol[i]
                            i += 1
                            param = ""
                            while i < len(protocol) and protocol[i] not in ('p','m','l','w'):
                                param += protocol[i]
                                i += 1
                            if cmd == 'p':
                                parts.append(f"place({param})")
                            elif cmd == 'm':
                                parts.append(f"mirror({param})")
                            elif cmd == 'l':
                                parts.append(f"linear({param})")
                            elif cmd == 'w':
                                parts.append(f"wave({param})")
                        print(f"protocol: {' '.join(parts)}")
                        print(f"input: {text}")
                        print(f"output: {encrypted}")
                        print(f"decrypted: {decrypted}")
                        if is_ok:
                            print("✅ FUNCTION IS CORRECT")
                        else:
                            print("❌ FUNCTION ERROR")
                            print("⚠️ REPORT TO OWNER")
                else:
                    mode = "encrypt" if choice == "1" else "decrypt"
                    result = process_protocol(protocol, text, mode)
                    if data.startswith('#'):
                        name = data[1:].split('/', 1)[0]
                        print(f"\nProtocol: {protocols[name]} ({name})")
                        print(f"Result: {result}")
                    else:
                        print(f"\n{protocol}/{result}")
                    
                    if choice == "1":
                        check = process_protocol(protocol, result, "decrypt")
                        if check == text:
                            print("\n-----no errors detected-----")
                        else:
                            print("\n⚠️ERROR! MISMATCH DETECTED!⚠️")
                            print("check function in main menu (3)")
            except Exception as e:
                print(f"\n⚠️ Error: {e}")
            input("\nPress Enter to continue...")
            break

if __name__ == "__main__":
    main()
