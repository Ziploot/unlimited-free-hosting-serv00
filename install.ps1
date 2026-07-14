# [ZipLoot] Serv00 Automated Deployer Launcher
# ==============================================
try {
    Clear-Host
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "   ZIPLOOT SERV00 AUTOMATED DEPLOYER" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host

    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    if ([string]::IsNullOrEmpty($scriptDir)) { $scriptDir = $pwd }
    Set-Location $scriptDir

    # Check if Python is installed
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        Write-Host "[ERROR] Python is not installed or not in your PATH." -ForegroundColor Red
        Write-Host "Please install Python 3 and try again." -ForegroundColor Yellow
        Read-Host "Press Enter to exit..."
        exit
    }

    # Run python deploy_serv00.py
    python -u deploy_serv00.py
} catch {
    Write-Host "[ERROR] An unexpected error occurred: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
}
