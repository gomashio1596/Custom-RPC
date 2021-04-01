import json
import re
import time
from ctypes import c_uint, create_unicode_buffer, pointer, windll, wintypes
from typing import Any

import psutil
from pypresence import Presence


def update(presence: Presence, process: psutil.Process, info: dict, *args: Any, **kwargs: Any) -> None:
    kwargs.setdefault('game_name', info['game_name'])

    def try_format(text: str):
        result = None
        if text is not None:
            try:
                result = text.format(*args, **kwargs)
            except (IndexError, KeyError):
                result = None
        return result

    presence.update(
        pid=process.pid,
        start=process.create_time(),
        large_image=info['large_image'] or None,
        large_text=info['game_name'],
        small_image=info['small_image'] or None,
        details=try_format(info['details']),
        state=try_format(info['state'])
    )


def start(process: psutil.Process, info: dict, *args: Any, **kwargs: Any) -> Presence:
    print(f"ゲームが {info['game_name']} に設定されました。RPCに接続します...")
    presence = Presence(info['client_id'])
    presence.connect()
    update(presence, process, info, *args, **kwargs)
    print('接続完了')
    return presence


if __name__ == '__main__':
    user32 = windll.user32

    with open('ignore.json', encoding='utf-8') as f:
        ignore = json.load(f)

    with open('rpc.json', encoding='utf-8') as f:
        rpc = json.load(f)

    def get_hwnd_by_pid(pid):
        hwnd = user32.GetTopWindow(None)
        while hwnd != 0:
            window_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, pointer(window_pid))
            title = get_window_text(hwnd)
            if (pid == window_pid.value
                    and title not in ignore):
                return hwnd
            hwnd = user32.GetWindow(hwnd, c_uint(2))  # GW_HWNDNEXT
        return None

    def get_window_text(hwnd):
        length = user32.GetWindowTextLengthW(hwnd) + 1
        buffer = create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buffer, length)
        return buffer.value

    def find_process():
        for index, p in enumerate(rpc):
            for process in psutil.process_iter(['name', 'exe', 'pid', 'create_time']):
                try:
                    if re.match(p['exe'], process.name()) and p['directory'] in process.exe():
                        return process, index
                except psutil.AccessDenied:
                    continue
        return None

    def check_foreground_process():
        hwnd = user32.GetForegroundWindow()
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, pointer(pid))
        process = psutil.Process(pid.value)
        for p in rpc:
            if re.match(p['exe'], process.name()) and p['directory'] in process.exe():
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
        hwnd = get_hwnd_by_pid(process.pid)
        while hwnd is None:
            time.sleep(1)
            hwnd = get_hwnd_by_pid(process.pid)
        match = re.match(info['title'], get_window_text(hwnd))
        if match is not None:
            args, kwargs = match.groups(), {k: v for k, v in match.groupdict().items() if v is not None}
            presence = start(process, info, *args, **kwargs)
        else:
            args = kwargs = None
            presence = start(process, info)
        while process.is_running():
            ret = check_foreground_process() or check_running_process()
            if ret is None:
                break

            foreground = check_foreground_process()
            current_process, current_info = ret
            if current_process.pid != process.pid or (foreground is not None and foreground[0].pid != process.pid):
                break
            
            hwnd = get_hwnd_by_pid(current_process.pid)
            while hwnd is None:
                time.sleep(1)
                hwnd = get_hwnd_by_pid(current_process.pid)
            match = re.match(current_info['title'], get_window_text(hwnd))
            if match is not None:
                current_args, current_kwargs = (
                    match.groups(),
                    {k: v for k, v in match.groupdict().items() if v is not None}
                )
                if current_args != args or current_kwargs != kwargs:
                    update(presence, current_process, current_info, *current_args, **current_kwargs)
            else:
                current_args = current_kwargs = None
                if current_args != args or current_kwargs != kwargs:
                    update(presence, current_process, current_info)
            args, kwargs = current_args, current_kwargs
                
            time.sleep(1)
        ret = check_foreground_process() or check_running_process()
        if not process.is_running() and ret is None:
            print(f"{info['game_name']} の終了を検知しました。RPCから切断します\n")
        presence.close()
