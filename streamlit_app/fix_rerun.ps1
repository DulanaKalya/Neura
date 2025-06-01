# PowerShell script to replace all instances of st.experimental_rerun() with st.rerun()
$files = Get-ChildItem -Path . -Include *.py -Recurse

foreach ($file in $files) {
    Write-Host "Processing $($file.FullName)"
    $content = Get-Content -Path $file.FullName -Raw
    if ($content -match "st\.experimental_rerun\(\)") {
        Write-Host "  Replacing in $($file.FullName)"
        $newContent = $content -replace "st\.experimental_rerun\(\)", "st.rerun()"
        Set-Content -Path $file.FullName -Value $newContent
    }
}

Write-Host "Done!"
