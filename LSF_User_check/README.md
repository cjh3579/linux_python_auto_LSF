# LSF Verilog 작업 모니터링 스크립트

이 저장소에는 Verilog 회귀 및 장기 실행 작업과 관련된 LSF 작업을 모니터링하기 위한 Python 스크립트와 CSH 래퍼가 포함되어 있습니다. 이 스크립트는 특정 큐에서 작업을 실행하고 있지만, 설정된 슬롯 제한에 포함되지 않은 사용자를 식별합니다. 이는 시스템 정책을 유지하고 모든 사용자가 리소스 할당 규칙을 준수하도록 하는 데 유용합니다.

---

## 목차
- [전제 조건](#전제-조건)
- [파일 설명](#파일-설명)
- [설정](#설정)
- [사용 방법](#사용-방법)
- [Cron 작업 설정](#cron-작업-설정)
- [스크립트 로직](#스크립트-로직)

---

## 전제 조건
- **LSF (Load Sharing Facility)**가 설치된 시스템.
- 표준 라이브러리(`os`, `subprocess`, `datetime`, `re`)에 접근 가능한 **Python 3**가 설치되어 있어야 합니다.
- 시스템에 **C-shell**(`csh`) 인터프리터가 있어야 합니다.
- 스크립트를 실행하고 지정된 디렉터리에 파일을 쓸 수 있는 올바른 권한이 필요합니다.

---

## 파일 설명
- `verilog_monitoring.py`: 모니터링 로직을 수행하는 핵심 Python 스크립트입니다. `bjobs`에서 사용자 목록을 추출하고, `blimits`에서 사용자 슬롯 제한을 확인하며, 불일치를 식별합니다.
- `run_verilog_monitoring.csh`: Cron 작업에 의해 실행되도록 설계된 CSH 래퍼 스크립트입니다. Python 스크립트를 실행하기 전에 필요한 LSF 환경 변수를 설정합니다.

---

## 설정
스크립트를 사용하기 전에 `verilog_monitoring.py`와 `run_verilog_monitoring.csh` 두 파일의 경로를 시스템에 맞게 구성해야 합니다.

### `verilog_monitoring.py`
다음 변수들을 조정하세요:
- `LSF_BASE_DIR`: LSF 시스템의 기본 설치 디렉터리입니다.
- `LSF_CONF_PATH`: LSF 구성 파일이 포함된 디렉터리입니다.
- `RESULT_DIR`: 출력 파일(사용자 목록)이 저장될 디렉터리입니다.
- `LSF_ENV_SCRIPT`: LSF 환경 설정 스크립트의 전체 경로(예: `env.csh`)입니다.
- `target_queues`: 모니터링할 LSF 큐 목록(예: `["verilog_regression", "verilog_long"]`)입니다.
- `user_pattern`: 특정 사용자를 일치시키기 위한 정규 표현식 패턴(예: `r"caev|snst"`)입니다.
- `target_name_prefix`: 확인하려는 `blimits` 구성 이름의 접두사(예: `"verilog_fdry_slotlimit_"`)입니다.

### `run_verilog_monitoring.csh`
다음 변수들을 조정하세요:
- `LSF_BASE_DIR`, `LSF_CONF_PATH`, `LSF_TOP`: 정확한 LSF 설치 경로를 가리켜야 합니다.
- `/path/to/your/log/directory/verilog_user.log`: 스크립트 실행 세부 정보가 기록될 로그 파일의 경로입니다.
- `/path/to/your/python3/bin/python3`: Python 3 인터프리터의 전체 경로입니다.
- `/path/to/your/verilog_monitoring.py`: Python 스크립트의 전체 경로입니다.
- `/path/to/your/lsf/env.csh`: LSF 환경 설정 스크립트의 경로입니다.

---

