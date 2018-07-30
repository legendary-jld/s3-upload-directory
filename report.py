import pickle
import os
from datetime import datetime

image_exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
video_exts = [".wmv", ".avi", ".mpg", ".mpeg", ".mov", ".mp4"]
audio_exts = [".mp3", ".wav", ".wma", ".ogg", ".midi", ".aif", ".aifc", ".aiff"]

accepted_exts = image_exts + video_exts + audio_exts

report = open("upload_reports/uploads_folder_report.pkl", "rb")
pkl_report = pickle.load(report, encoding="utf-8")

cntr = 0
perm_cntr = 0
data_size = 0
filename = "retry_{0}.txt".format(int(datetime.utcnow().timestamp()))
found_exts =  set()
with open(filename, "w") as retry_file:
    for item in pkl_report:
        if item.get('ext') in accepted_exts:
            st = os.stat(item.get("full_path"))
            file_permissions = str(st.st_mode)
            if not file_permissions in ("33206","777"): # 33206 linux equivalent for 777
                try:
                    os.chmod(item.get("full_path"), 0o666)
                    perm_cntr = perm_cntr + 1
                except Exception:
                    print("chmod failed:", item.get("full_path"))
                    break

            retry_file.write("{0},{1}\n".format(item.get("filename"), item.get("full_path")))
            cntr = cntr + 1
            data_size = data_size + item.get("file_size")
        else:
            found_exts.add(item.get("ext"))
            pass
retry_file.close()

print("{:,}".format(data_size/1000), "kb size")
print(cntr, "files")
if perm_cntr > 0:
    print(perm_cntr, "permissions modified")
# print(found_exts, "extenstions")
