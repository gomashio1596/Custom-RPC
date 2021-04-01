# Custom RPC
Discord Rich Presenceを好きなゲームで使うためのプログラム  
アクティブなウィンドウが優先的にRPCに接続される  

# ignore.json
文字列 (string) のリスト  
除外するウィンドウタイトルを書く  

# rpc.json
[RPC Info](#RPC-Info) のリスト

## RPC Info
|  キー  |  型  |  説明  |
| --- | --- | --- |
|  game_name  |  文字列 (String)  |  ログに表示されるゲーム名  |
|  title  |  文字列 (String)  |  ゲームのウィンドウタイトル。正規表現が使える  |
|  exe  |  文字列 (String)  |  プロセスの実行ファイル名 (拡張子を含む)  |
|  directory  |  文字列 (String)  |  実行ファイルが入っているディレクトリ名  |
|  client_id  |  文字列 (String)  |  RPCに使うDiscordのアプリケーションのCLIENT ID  |
|  large_image  |  文字列、null (String, null)  |  RPCに大画像として表示するアセットのアセット名  |
|  small_image  |  文字列、null (String, null)  |  RPCに小画像として表示するアセットのアセット名  |
|  details  |  文字列、null (String, null)  |  RPCの説明文の1行目に表示するテキスト<br>titleでの正規表現のグループとgame_name変数が使える  |
|  state  |  文字列、null (String, null)  |  RPCの説明文の2行目に表示するテキスト<br>titleでの正規表現のグループとgame_name変数が使える  |
