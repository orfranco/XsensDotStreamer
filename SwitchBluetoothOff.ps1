Get-PnpDevice -Class "Bluetooth" -Present | ForEach-Object {
  Enable-PnpDevice -InstanceID $_.InstanceID  -Confirm:$false
 }
