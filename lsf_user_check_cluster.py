import os
import subprocess
import datetime
import re

# --- 1. 환경 변수 설정 ---
LSF_BASE_DIR = '/path/to/lsf_install_dir'
LSF_BIN_PATH = os.path.join(LSF_BASE_DIR, 'bin')
LSF_ETC_PATH = os.path.join(LSF_BASE_DIR, 'etc')
LSF_LIB_PATH = os.path.join(LSF_BASE_DIR, 'lib')
LSF_CONF_PATH = '/path/to/lsf/conf'

os.environ['PATH'] = f"{LSF_BIN_PATH}:{os.environ.get('PATH', '')}"
os.environ['LSF_BINDIR'] = LSF_BIN_PATH
os.environ['LSF_SERVERDIR'] = LSF_ETC_PATH
os.environ['LSF_LIBDIR'] = LSF_LIB_PATH
os.environ['LSF_ENVDIR'] = LSF_CONF_PATH

# --- 2. 결과 저장 디렉토리 ---
RESULT_DIR = "./results"
DATE_SUFFIX = datetime.datetime.now().strftime("%Y%m%d_%H%M")
TODAY_DATE = datetime.datetime.now().strftime("%Y%m%d")

BJOBS_TEMP_FILE = os.path.join(RESULT_DIR, "bjobs_users.txt")
LSB_LIMIT_TEMP_FILE = os.path.join(RESULT_DIR, "lsb_limit_users.txt")
DAILY_UNIQUE_ACCOUNTS_FILE = os.path.join(RESULT_DIR, f"daily_accounts_{TODAY_DATE}.txt")

os.makedirs(RESULT_DIR, exist_ok=True)

LSF_ENV_SCRIPT = "/path/to/lsf/env.csh"

# --- 3. LSF 환경 로드 ---
def load_lsf_environment(script_path):
    try:
        command_to_get_env = f"csh -c 'source {script_path} && env'"
        env_output = subprocess.check_output(command_to_get_env, shell=True, encoding='utf-8')
        for line in env_output.splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    except Exception as e:
        print(f"[ERROR] LSF 환경 로딩 실패: {e}")
        exit(1)

load_lsf_environment(LSF_ENV_SCRIPT)

# --- 4. 쉘 명령 실행 함수 ---
def run_shell_command(command_str):
    try:
        result = subprocess.run(
            command_str,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            env=os.environ
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 명령 실행 실패: {e.stderr.strip()}")
        raise

# --- 5. bjobs 사용자 추출 ---
def get_bjobs_users_from_queues(queue_names):
    users = set()
    bjobs_cmd = os.path.join(os.environ['LSF_BINDIR'], 'bjobs')
    for queue in queue_names:
        command = f"{bjobs_cmd} -q \"{queue}\" -u all -o USER | grep -E \"dev|test\" | awk '{{print $1}}'"
        try:
            output = run_shell_command(command).splitlines()
            for user in output[1:]:
                if user.strip():
                    users.add(user.strip())
        except Exception:
            continue
    return users

# --- 6. blimits 사용자 추출 ---
def get_blimits_users_from_consume_limits(queue_names, target_prefix):
    users = set()
    blimits_cmd = os.path.join(os.environ['LSF_BINDIR'], 'blimits')
    for queue in queue_names:
        command = f"{blimits_cmd} -q \"{queue}\" -c"
        try:
            output = run_shell_command(command)
            blocks = re.findall(r'Begin Limit(.*?)End Limit', output, re.DOTALL)
            for block in blocks:
                name_match = re.search(r'NAME\s*[:=]\s*(\S+)', block)
                user_match = re.search(r'PER_USER\s*[:=]\s*(.+)', block)
                if name_match and user_match:
                    name = name_match.group(1).strip()
                    if name.startswith(target_prefix):
                        data = user_match.group(1).replace('(', '').replace(')', '')
                        found_users = re.findall(r'\b[a-zA-Z0-9_]+\b', data)
                        users.update(found_users)
        except Exception:
            continue
    return users

# --- 7. 메인 로직 ---
target_queues = ["example_queue_1", "example_queue_2"]
all_bjobs_users = get_bjobs_users_from_queues(target_queues)
with open(BJOBS_TEMP_FILE, 'w') as f:
    f.writelines([user + '\n' for user in sorted(all_bjobs_users)])

lsb_limit_users = get_blimits_users_from_consume_limits(target_queues, "example_slotlimit_")
with open(LSB_LIMIT_TEMP_FILE, 'w') as f:
    f.writelines([user + '\n' for user in sorted(lsb_limit_users)])

missing_users = all_bjobs_users - lsb_limit_users
existing_users = set()
if os.path.exists(DAILY_UNIQUE_ACCOUNTS_FILE):
    with open(DAILY_UNIQUE_ACCOUNTS_FILE, 'r') as f:
        existing_users = set(line.strip() for line in f)

with open(DAILY_UNIQUE_ACCOUNTS_FILE, 'w') as f:
    f.writelines([user + '\n' for user in sorted(existing_users.union(missing_users))])

for file in [BJOBS_TEMP_FILE, LSB_LIMIT_TEMP_FILE]:
    try:
        os.remove(file)
    except Exception:
        pass

print("[INFO] 스크립트 실행 완료")
