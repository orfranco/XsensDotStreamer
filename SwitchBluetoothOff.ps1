Get-PnpDevice -Class "bluetooth" | ForEach-Object {
  Enable-PnpDevice -InstanceID $_.InstanceID  -Confirm:$false
 }
