'''
Google Drive Uploader for Windows
'''
from PIL import Image
from tkinter import messagebox
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials
import tkinter as tk
import os, glob, logging, shutil, getpass

import numpy as np

logger = logging.getLogger()
logger.setLevel(logging.INFO)

## 編集済画像格納先
TARGET_ORIGIN_FOLDER = "/Users/" + getpass.getuser()
## USBメモリ名
USB_FOLDER = "/Volumes/USB画像"
## ロゴ画像格納フォルダ名
LOGO_FOLDER = "/Users/" + getpass.getuser() + "/desktop/画像ロゴ"
## Jsonファイル名
JSON_KEY_FILE = './service-account-key.json'
## PCに編集済画像フォルダを残す場合はFalse
DELETE_LOCAL_FOLDER = True
## GoogleDrive保存先フォルダの後尾コード
GOOGLE_DRIVE_FOLDER_CODE = '{google drive フォルダコード}'


class Application(tk.Frame):
    def __init__(self, notice, default_value, check_pattern, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.entry_text = 0
        self.check_pattern = check_pattern
        self.create_widgets(notice, default_value, check_pattern)

    def create_widgets(self, notice, default_value, check_pattern):
        self.label = tk.Label(
            text=notice)
        self.label.pack()

        self.entry_box = tk.Entry(width=30)
        self.entry_box.insert(tk.END, default_value)
        self.entry_box.pack()

        self.button = tk.Button(text=u'入力完了', width=20)
        self.button.bind("<Button-1>", self.get_and_delete_value)
        self.button.pack()

    def get_and_delete_value(self, event):
        if self.check_pattern == 1:
            try:
                self.entry_text = int(self.entry_box.get())
            except ValueError as e:
                messagebox.showerror('エラー', '半角数値で入力してください')
                self.get_and_delete_value(self, event)
        elif self.check_pattern == 2:
            if self.entry_box.get().encode('utf-8').isalnum() is True:
                self.entry_text = self.entry_box.get()
            else:
                messagebox.showerror('エラー', '半角英数値で入力してください')
                print(self.entry_box.get())
                self.get_and_delete_value(self, event)
        else:
            self.entry_text = self.entry_box.get()

        self.entry_box.delete(0, tk.END)
        root.destroy()
        root.quit()
        exit()

## 画像処理
def edit_image(image_file_path):
    try:
        image = Image.open(image_file_path).convert("RGB")
    except:
        return None

    image_name = image_file_path.split("/")[-1]
    image_save_path = new_dir + "/" + image_name

    # リサイズ処理
    resized_image = image.resize((1280, 1280))
    resized_image.save(image_save_path)

    # 画像貼り付け
    top_margin = 640 - int(int(logo_image.height) / 2)
    resized_image.paste(logo_image, (544, top_margin), logo_image.split()[3])
    pasted_image_save_path = new_dir + "/" + "(ロゴ付き)" + image_name
    resized_image.resize((1280, 1280)).save(pasted_image_save_path)

    return [image_save_path, pasted_image_save_path]


## GoogleApi認証処理
def getGoogleService():
    scope = ['https://www.googleapis.com/auth/drive.file']
    keyFile = JSON_KEY_FILE
    credentials = ServiceAccountCredentials.from_json_keyfile_name(keyFile, scopes=scope)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)

## GoogleDriveへフォルダ作成
def createFolderToGoogleDrive(drive, folderName):
    mimeType = 'application/vnd.google-apps.folder'
    file_metadata = {"name": folderName, "mimeType": mimeType, "parents": [GOOGLE_DRIVE_FOLDER_CODE] }
    response = drive.files().create(body=file_metadata).execute()
    return response["id"]

## GoogleDriveへファイルアップロード
def uploadFileToGoogleDrive(drive, fileName, filePath, DriveFolderPath):
    try:
        ext = os.path.splitext(filePath.lower())[1][1:]
        if ext == "jpg":
            ext = "jpeg"
        mimeType = "image/" + ext

        service = getGoogleService()
        file_metadata = {"name": fileName, "mimeType": mimeType, "parents": [DriveFolderPath] }
        media = MediaFileUpload(filePath, mimetype=mimeType, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    except Exception as e:
        logger.exception(e)


## 画像アップロード実行処理
def upload_to_GD(folder_name, binary_list, DELETE_LOCAL_FOLDER):
    # 画像アップロード
    drive = getGoogleService()
    folder_name = folder_name.split("/")[-1]
    drive_folder_path = createFolderToGoogleDrive(drive, folder_name)
    for path_list in binary_list:
        for file_path in path_list:
            file_name = file_path.split("/")[-1]
            uploadFileToGoogleDrive(drive, file_name, file_path, drive_folder_path)

    # ローカル削除処理
    if DELETE_LOCAL_FOLDER == True:
        shutil.rmtree(new_dir)
    print('----------------------------------')
    print('____アップロード完了____')
    print('保存先：{}'.format(folder_name[0]))
    print('保存数：{}'.format(len(binary_list)))
    print('----------------------------------')


if __name__ == "__main__":

    folder_name = ''
    if TARGET_ORIGIN_FOLDER[-1] == "/":
        folder_name = TARGET_ORIGIN_FOLDER
    else:
        folder_name = TARGET_ORIGIN_FOLDER + "/"

    # フォルダ作成のためのダイアログの元情報
    # タイトル、注意書き、入力例、入力規則(0：制限なし、1：半角数値のみ、2：半角英数字のみ)
    folder_name_inputs_list = [
        ["物件名", "全角カタカナのみ", "ヘイワハイツ", 0],
        ["号室", "半角数値のみ", "101", 2],
        ["住所－１", "市区町村", "渋谷区渋谷", 0],
        ["住所－２", "丁目～番地（半角数値で入力）", "1-1-1", 0],
        ["間取り", "半角英数値のみ", "1LDK", 2],
        ["平米数", "半角数値のみ(m2)", "30", 2]
    ]

    # ダイアログ生成開始
    for num_input in range(len(folder_name_inputs_list)):
        root = tk.Tk()
        root.title(folder_name_inputs_list[num_input][0]+"を入力してください")
        # ウインドウサイズを定義する
        root.geometry('400x300')

        app = Application(
            folder_name_inputs_list[num_input][1],
            folder_name_inputs_list[num_input][2],
            folder_name_inputs_list[num_input][3],
            master=root
        )
        app.mainloop()
        folder_name = folder_name + " " + str(app.entry_text)

    new_dir = folder_name

    # フォルダ作成
    try:
        os.mkdir(new_dir)
    except:
        pass

    logo_image_picture = LOGO_FOLDER + "/ロゴ画像.png"
    logo_image = Image.open(logo_image_picture)

    # ロゴ画像が背景透過されていた場合の処理
    if logo_image.mode == 'RGBA':
        logo_image = logo_image.resize((192, int(logo_image.height * 192 / int(logo_image.width))))
        logo_image = np.array(logo_image)
        logo_image[logo_image[..., 3] != 0, 3] = 25
        logo_image = Image.fromarray(logo_image)
    else:
        logo_image = logo_image.resize((192, int(logo_image.height * 192 / int(logo_image.width))))
        logo_image.putalpha(25)

    usb_folder_search = USB_FOLDER + "/*"

    binary_list = [edit_image(file) for file in glob.glob(usb_folder_search)]

    upload_to_GD(folder_name, binary_list, DELETE_LOCAL_FOLDER)
