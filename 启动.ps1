if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path += ";$env:USERPROFILE\.cargo\bin"
}

echo "正在配置依赖。"
uv run sd_auto_sign.py

if ($LASTEXITCODE -ne 0) {
    echo "正在下载内核。"
    uv run python -m playwright install chromium
    uv run sd_auto_sign.py
}

pause
