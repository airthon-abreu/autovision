Set WshShell = CreateObject("WScript.Shell")
' O zero (0) no final é o comando mágico do Windows para "Executar invisível"
WshShell.Run chr(34) & "INICIAR_SISTEMA.bat" & Chr(34), 0
Set WshShell = Nothing