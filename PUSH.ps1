$ErrorActionPreference = "Stop"
$source = $PSScriptRoot
$remote = "https://github.com/Navid-Ishaq/read-detleng.git"

function Git-Run {
    & git @args
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed. Push stopped."
    }
}

Push-Location -LiteralPath $source
try {
    if (!(Test-Path "content" -PathType Container) -or
        !(Test-Path "tools\build.py" -PathType Leaf)) {
        throw "Project files missing. Push stopped."
    }

    # Keep empty topic folders visible in Git.
    Get-ChildItem "content" -Directory -Recurse |
        ForEach-Object {
            $items = @(Get-ChildItem -LiteralPath $_.FullName -Force)
            if ($items.Count -eq 0) {
                New-Item -ItemType File `
                    -Path (Join-Path $_.FullName ".gitkeep") |
                    Out-Null
            }
        }

    python tools/build.py
    if ($LASTEXITCODE -ne 0) {
        throw "Document build failed. Nothing pushed."
    }

    if (!(Test-Path ".git")) {
        Git-Run init -b main
        Git-Run remote add origin $remote
        Git-Run fetch origin main

        # Adopt existing GitHub history; preserve local files.
        Git-Run reset --mixed origin/main
    }
    else {
        $actualRemote = & git remote get-url origin
        if ($LASTEXITCODE -ne 0 -or $actualRemote -ne $remote) {
            throw "Unexpected repository. Push stopped."
        }

        $branch = & git branch --show-current
        if ($LASTEXITCODE -ne 0 -or $branch -ne "main") {
            throw "Please use the main branch."
        }

        Git-Run fetch origin main

        $head = & git rev-parse HEAD
        if ($LASTEXITCODE -ne 0) { throw "Cannot read local HEAD." }

        $remoteHead = & git rev-parse origin/main
        if ($LASTEXITCODE -ne 0) { throw "Cannot read remote HEAD." }

        if ($head -ne $remoteHead) {
            Git-Run merge-base --is-ancestor origin/main HEAD
            # Allows retrying a previously committed but unpushed update.
        }
    }

    # Exclude generated output and local backup files.
    $exclude = ".git\info\exclude"
    @(
        "/_site/"
        "/.openai/"
        "__pycache__/"
        "*.pyc"
        "*.bak"
    ) | Add-Content -LiteralPath $exclude -Encoding utf8

    Git-Run add --all

    & git diff --cached --quiet
    $diffCode = $LASTEXITCODE

    if ($diffCode -eq 1) {
        Git-Run commit -m (
            "Update reading library " +
            (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        )
    }
    elseif ($diffCode -ne 0) {
        throw "Cannot check staged changes."
    }

    Git-Run push origin main

    Write-Host ""
    Write-Host "Library sync complete, janab!" -ForegroundColor Green
    Write-Host "GitHub Actions will publish any new commit."
}
finally {
    Pop-Location
}
