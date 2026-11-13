
$code = @"
using System;
using System.Runtime.InteropServices;

public class HuaweiWmi {
    [DllImport(@"C:\Program Files\Huawei\PCManager\WmiUtil.dll",
        EntryPoint = "?SetKeyboardLightTime@BiosWmi@HwSDK@@SAHG@Z")]
    public static extern int SetKeyboardLightTime(ushort seconds);

    [DllImport(@"C:\Program Files\Huawei\PCManager\WmiUtil.dll",
        EntryPoint = "?GetKeyboardLightTime@BiosWmi@HwSDK@@SAHAEAG@Z")]
    public static extern int GetKeyboardLightTime(out ushort seconds);
}
"@

Add-Type -TypeDefinition $code

# Set keyboard backlight timeout to 900 seconds (15 minutes)
$setResult = [HuaweiWmi]::SetKeyboardLightTime(900)

Write-Host "Set operation returned: $setResult" -ForegroundColor Cyan

# Read the current keyboard backlight timeout
[uint16]$sec = 0
$getResult = [HuaweiWmi]::GetKeyboardLightTime([ref]$sec)

# Display the results
if ($getResult -eq 0) {
    Write-Host "Keyboard backlight timeout: $sec seconds ($([math]::Round($sec / 60, 1)) minutes)" -ForegroundColor Green
}
else {
    Write-Host "Failed to read keyboard backlight timeout. Error code: $getResult" -ForegroundColor Red
}
