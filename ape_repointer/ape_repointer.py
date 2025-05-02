import os
import re
import sys

def parse_all_addresses(bank_folder):
    address_map = {}
    for filename in os.listdir(bank_folder):
        if filename.lower().startswith("bank") and filename.endswith(".txt"):
            path = os.path.join(bank_folder, filename)
            with open(path, "r", encoding="utf-8", errors="ignore") as file:
                for line in file:
                    match = re.match(r"^\s*([0-9A-Fa-f]{6}):", line)
                    if match:
                        address = match.group(1).upper()
                        file_id = filename.lower()
                        address_map.setdefault(file_id, {})[address] = True
    return address_map

def build_us_to_jp_map(us_folder, jp_folder):
    us_addresses = parse_all_addresses(us_folder)
    jp_addresses = parse_all_addresses(jp_folder)
    us_to_jp = {}

    for bank_file in us_addresses:
        if bank_file in jp_addresses:
            us_keys = sorted(us_addresses[bank_file])
            jp_keys = sorted(jp_addresses[bank_file])

            # Match addresses by order
            for us_addr, jp_addr in zip(us_keys, jp_keys):
                us_to_jp[us_addr] = jp_addr
    return us_to_jp

def replace_addresses_in_ccs(input_folder, output_folder, us_to_jp):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pointer_pattern = re.compile(r"\b(0x)?([0-9A-Fa-f]{6})\b")

    for filename in os.listdir(input_folder):
        if filename.endswith(".ccs"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            with open(input_path, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()

            def repl(match):
                prefix, hex_value = match.groups()
                upper_val = hex_value.upper()
                if upper_val in us_to_jp:
                    new_val = us_to_jp[upper_val]
                    return f"0x{new_val}" if prefix else new_val
                return match.group(0)

            new_content = pointer_pattern.sub(repl, content)

            with open(output_path, "w", encoding="utf-8") as out_file:
                out_file.write(new_content)

def main():
    if len(sys.argv) != 2:
        print("Usage: python ape_repointer.py <path_to_eb-listing>")
        sys.exit(1)

    eb_listing_path = sys.argv[1]
    us_folder = os.path.join(eb_listing_path, "US")
    jp_folder = os.path.join(eb_listing_path, "JP")

    if not os.path.isdir(us_folder) or not os.path.isdir(jp_folder):
        print("eb-listing must contain 'US' and 'JP' subfolders.")
        sys.exit(1)

    us_to_jp = build_us_to_jp_map(us_folder, jp_folder)
    replace_addresses_in_ccs(".", "output", us_to_jp)
    print("Done. Output written to ./output")

if __name__ == "__main__":
    main()
