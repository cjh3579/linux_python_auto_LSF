#!/bin/csh -f

# ----------------------------------------------------
# [CRONTAB EXECUTION LOG]
# Logs the start time of this script.
echo "----------------------------------------------------" >> /path/to/your/log/directory/verilog_user.log
echo "[`date '+%Y-%m-%d %H:%M:%S'`] Starting run_verilog_monitoring.csh for verilog monitoring." >> /path/to/your/log/directory/verilog_user.log
echo "----------------------------------------------------" >> /path/to/your/log/directory/verilog_user.log

# --- Set LSF Environment Variables ---
# IMPORTANT: The following paths must be accurate for LSF commands to work.
setenv LSF_BASE_DIR /path/to/your/lsf/installation/10.1/linux2.6-glibc2.3-x86_64
setenv LSF_BIN_PATH ${LSF_BASE_DIR}/bin
setenv LSF_ETC_PATH ${LSF_BASE_DIR}/etc
setenv LSF_LIB_PATH ${LSF_BASE_DIR}/lib
setenv LSF_CONF_PATH /path/to/your/lsf/conf

# Add LSF binary path to the beginning of the PATH environment variable.
setenv PATH ${LSF_BIN_PATH}:${PATH}

# Set essential LSF variables.
setenv LSF_BINDIR ${LSF_BIN_PATH}
setenv LSF_SERVERDIR ${LSF_ETC_PATH}
setenv LSF_LIBDIR ${LSF_LIB_PATH}
setenv LSF_ENVDIR ${LSF_CONF_PATH}
setenv LSF_TOP /path/to/your/lsf/installation/10.1 # <-- Verify this is the top-level LSF installation path!

# Add LSF library path to LD_LIBRARY_PATH. (Crucial for LSF commands)
setenv LD_LIBRARY_PATH ${LSF_LIB_PATH}:${LD_LIBRARY_PATH}

# --- Source LSF Environment Script (Recommended) ---
# Sourcing this script is recommended as it might contain additional system-specific settings.
echo "[`date '+%Y-%m-%d %H:%M:%S'`] Attempting to source LSF environment script..." >> /path/to/your/log/directory/verilog_user.log
source /path/to/your/lsf/env.csh >> /path/to/your/log/directory/verilog_user.log 2>&1
echo "[`date '+%Y-%m-%d %H:%M:%S'`] LSF environment script sourcing completed." >> /path/to/your/log/directory/verilog_user.log

# --- Execute Python Script ---
# The Python script will inherit all necessary environment variables from this CSH script.
echo "[`date '+%Y-%m-%d %H:%M:%S'`] Attempting to execute Python script..." >> /path/to/your/log/directory/verilog_user.log
(/path/to/your/python3/bin/python3 /path/to/your/verilog_monitoring.py >> /path/to/your/log/directory/verilog_user.log 2>&1)

# Log the script's completion time.
echo "[`date '+%Y-%m-%d %H:%M:%S'`] Script execution finished." >> /path/to/your/log/directory/verilog_user.log
