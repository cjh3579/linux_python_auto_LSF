import os
import subprocess
import datetime
import re

# --- 1. Environment Variable Configuration ---
# Set LSF binary and configuration paths to support LSF command execution.
# IMPORTANT: Adjust these paths to match your specific LSF installation.
LSF_BASE_DIR = os.environ.get('LSF_BASE_DIR', '/path/to/your/lsf/installation')
LSF_BIN_PATH = os.path.join(LSF_BASE_DIR, 'bin')
LSF_ETC_PATH = os.path.join(LSF_BASE_DIR, 'etc')
LSF_LIB_PATH = os.path.join(LSF_BASE_DIR, 'lib')
LSF_CONF_PATH = os.environ.get('LSF_CONF_PATH', '/path/to/your/lsf/conf')

os.environ['PATH'] = f"{LSF_BIN_PATH}:{os.environ.get('PATH', '')}"
os.environ['LSF_BINDIR'] = LSF_BIN_PATH
os.environ['LSF_SERVERDIR'] = LSF_ETC_PATH
os.environ['LSF_LIBDIR'] = LSF_LIB_PATH
os.environ['LSF_ENVDIR'] = LSF_CONF_PATH

# --- 2. Script Settings and File Path Definitions ---
# IMPORTANT: Define the directory where result files will be saved.
RESULT_DIR = os.environ.get('RESULT_DIR', '/path/to/your/result/directory')

# Specify current date and time format (YYYYMMDD_HHMM)
DATE_SUFFIX = datetime.datetime.now().strftime("%Y%m%d_%H%M")
TODAY_DATE = datetime.datetime.now().strftime("%Y%m%d")

# Define result file paths
BJOBS_TEMP_FILE = os.path.join(RESULT_DIR, "bjobs_users.txt")
LSB_LIMIT_TEMP_FILE = os.path.join(RESULT_DIR, "lsb_limit_users.txt")
DAILY_UNIQUE_ACCOUNTS_FILE = os.path.join(RESULT_DIR, f"verilog_daily_unique_accounts_{TODAY_DATE}.txt")

# Create the result directory if it doesn't exist
os.makedirs(RESULT_DIR, exist_ok=True)

# LSF environment configuration script path (needs to be loaded before script execution)
LSF_ENV_SCRIPT = os.environ.get('LSF_ENV_SCRIPT', '/path/to/your/lsf/env.csh')

# --- 3. Load LSF Environment ---
# Reflect necessary environment variables for LSF commands in the current Python environment.
def load_lsf_environment(script_path):
    print(f"Loading LSF environment script '{script_path}'...")
    try:
        command_to_get_env = f"csh -c 'source {script_path} && env'"
        env_output = subprocess.check_output(command_to_get_env, shell=True, universal_newlines=True, encoding='utf-8')
        
        for line in env_output.splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
        print("LSF environment variables loaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to load LSF environment script. Stderr: {e.stderr}")
        exit(1)
    except Exception as e:
        print(f"Error: Problem occurred while parsing LSF environment variables: {e}")
        exit(1)

# Only load environment if not already set (e.g., when run by csh wrapper)
if not os.environ.get('LSF_LOADED'):
    load_lsf_environment(LSF_ENV_SCRIPT)
    os.environ['LSF_LOADED'] = 'true'

# --- 4. Shell Command Execution Helper Function ---
# Executes shell commands and returns the result.
def run_shell_command(command_str):
    try:
        result = subprocess.run(
            command_str,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            env=os.environ
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: Command '{command_str}' failed. Stderr: {e.stderr.strip()}")
        raise
    except FileNotFoundError:
        print(f"Error: Command not found. Check PATH settings: '{command_str}'")
        raise

# --- 5. Extract Users from bjobs ---
# Get user lists from specified queues with a specific pattern.
def get_bjobs_users_from_queues(queue_names, user_pattern):
    print(f"1. Extracting user list from '{', '.join(queue_names)}' queues with bjobs command...")
    all_users = set()
    
    bjobs_cmd = os.path.join(os.environ.get('LSF_BINDIR', 'bjobs'))
    
    for queue_name in queue_names:
        # Use a more robust command without pipes for cleaner error handling in Python
        try:
            output_lines = run_shell_command(f"{bjobs_cmd} -q \"{queue_name}\" -u all -o \"USER\"").splitlines()
            
            # Filter users based on the provided pattern
            pattern = re.compile(user_pattern)
            for user_line in output_lines[1:]: # Skip the first header line
                user = user_line.strip()
                if user and pattern.search(user):
                    all_users.add(user)
        except Exception as e:
            print(f"Warning: Failed to extract users from '{queue_name}' queue: {e}")
            continue

    return all_users

target_queues = ["verilog_regression", "verilog_long"]
user_pattern = r"caev|snst" # Example user patterns
all_bjobs_users = get_bjobs_users_from_queues(target_queues, user_pattern)

with open(BJOBS_TEMP_FILE, 'w', encoding='utf-8') as f:
    for user in sorted(list(all_bjobs_users)):
        f.write(f"{user}\n")

if not all_bjobs_users:
    print("Warning: The user list extracted by bjobs is empty. Check queue names or user filters.")
print(f"bjobs user list saved to '{BJOBS_TEMP_FILE}'.")

print("-" * 50)

# --- 6. Extract PER_USER Limit Accounts from blimits -c ---
# Check consume limits for each queue and extract specific PER_USER limits.
def get_blimits_users_from_consume_limits(queue_names, target_name_prefix):
    print(f"2. Extracting PER_USER limit users from 'blimits -q <queue> -c' (NAME prefix: '{target_name_prefix}')...")
    
    limit_users = set()
    blimits_cmd = os.path.join(os.environ.get('LSF_BINDIR', 'blimits'))

    for queue_name in queue_names:
        command_str = f"{blimits_cmd} -q \"{queue_name}\" -c"
        
        try:
            blimits_output = run_shell_command(command_str)

            limit_blocks_regex = re.compile(r'Begin Limit\s*(.*?)\s*End Limit', re.DOTALL)
            found_blocks = limit_blocks_regex.findall(blimits_output)
            
            if not found_blocks:
                print(f"  - Warning: Did not find 'Begin Limit'/'End Limit' blocks in '{queue_name}' queue. Limits may not exist.")
                continue

            for block_content in found_blocks:
                block_name = ""
                per_user_data = ""
                
                name_match = re.search(r'^\s*NAME[\s\t]*[:=][\s\t]*(\S+)', block_content, re.MULTILINE)
                if name_match:
                    block_name = name_match.group(1).strip()
                
                per_user_match = re.search(r'^\s*PER_USER[\s\t]*[:=][\s\t]*(.+)', block_content, re.MULTILINE)
                if per_user_match:
                    per_user_data = per_user_match.group(1).strip().replace('(', '').replace(')', '').strip()

                if block_name.startswith(target_name_prefix) and per_user_data:
                    print(f"  - Matching Limit block found (NAME: '{block_name}'). Extracting users...")
                    
                    users_in_block = re.findall(r'\b[a-zA-Z0-9_]+\b', per_user_data)
                    
                    if users_in_block:
                        print(f"  - Added {len(users_in_block)} users from '{block_name}'.")
                        for user in users_in_block:
                            limit_users.add(user)
                
        except Exception as e:
            print(f"Error: An error occurred while executing or parsing 'blimits -q {queue_name} -c': {e}")
            continue

    return limit_users

lsb_limit_users = get_blimits_users_from_consume_limits(target_queues, "verilog_fdry_slotlimit_")

with open(LSB_LIMIT_TEMP_FILE, 'w', encoding='utf-8') as f:
    for user in sorted(list(lsb_limit_users)):
        f.write(f"{user}\n")

if not lsb_limit_users:
    print("Warning: No PER_USER limit accounts found with blimits command. Check your LSF configuration or command output.")
print(f"blimits PER_USER limit user list saved to '{LSB_LIMIT_TEMP_FILE}'.")

print("-" * 50)

# --- 7. Compare Two Account Lists and Generate Result ---
print("3. Comparing two files and generating results (accounts in bjobs but not in the limit list)...")

missing_from_limit = all_bjobs_users - lsb_limit_users

if missing_from_limit:
    existing_daily_accounts = set()
    if os.path.exists(DAILY_UNIQUE_ACCOUNTS_FILE):
        with open(DAILY_UNIQUE_ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                existing_daily_accounts.add(line.strip())

    updated_daily_accounts = existing_daily_accounts.union(missing_from_limit)

    with open(DAILY_UNIQUE_ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        for user in sorted(list(updated_daily_accounts)):
            f.write(f"{user}\n")
    print(f"Daily unique account list updated in '{DAILY_UNIQUE_ACCOUNTS_FILE}'.")
else:
    print(f"No new accounts detected. '{DAILY_UNIQUE_ACCOUNTS_FILE}' remains unchanged.")

# --- 8. Delete Temporary Files ---
# Clean up temporary files created after script execution.
try:
    os.remove(BJOBS_TEMP_FILE)
    os.remove(LSB_LIMIT_TEMP_FILE)
except OSError as e:
    print(f"Error occurred while deleting temporary files: {e}")

print("Script execution completed.")
