import json
import time
from ctypes import pointer, windll, wintypes
from typing import Optional, Tuple

import psutil
from pypresence import Presence


def start(process: psutil.Process, info: dict) -> Presence:
    print(f"ゲームが {info['game_name']} に設定されました。RPCに接続します...")
    presence = Presence(info['client_id'])
    presence.connect()
    presence.update(
        pid=process.pid,
        start=process.create_time(),
        large_image=info['large_image'] or None,
        large_text=info['game_name'],
        small_image=info['small_image'] or None,
        details=f"{info['game_name']}をプレイ中",
        state=info['state']
    )
    print('接続完了')
    return presence


if __name__ == '__main__':
    user32 = windll.user32

    with open('rpc.json', encoding='utf-8') as f:
        rpc = json.load(f)

    def find_process() -> Optional[Tuple[psutil.Process, int]]:
        for index, p in enumerate(rpc):
            for process in psutil.process_iter(['name','exe','pid','create_time']):
                if process.name() == p['exe'] and p['directory'] in process.exe():
                    return process, index
        return None

    def check_foreground_process():
        hwnd = user32.GetForegroundWindow()
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, pointer(pid))
        process = psutil.Process(pid.value)
        for p in rpc:
            if process.name() == p['exe'] and p['directory'] in process.exe():
                return process, p
        else:
            return None

    def check_running_process():
        ret = find_process()
        if ret is not None:
            return ret[0], rpc[ret[1]]
        return None

    def get_rpc_process():
        ret = check_foreground_process() or check_running_process()
        while ret is None:
            ret = check_foreground_process() or check_running_process()
            time.sleep(1)
        return ret

    print('ゲームの起動を待っています...')
    while True:
        process, info = get_rpc_process()
        presence = start(process, info)
        while process.is_running():
            ret = check_foreground_process() or check_running_process()
            if ret is not None and check_foreground_process() is not None and ret[1] != info:
                break
            time.sleep(1)
        ret = check_foreground_process() or check_running_process()
        if not process.is_running() and ret is None:
            print(f"{info['game_name']} の終了を検知しました。RPCから切断します\n")
        presence.close()
