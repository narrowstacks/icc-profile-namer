# ICC Profile Organizer

A smart tool that automatically organizes ICC color profiles, EMX/EMY2 files, and PDFs by printer model and paper brand, with support for flexible printer name mappings and profile remappings.

## Setup

### Using a Virtual Environment (Recommended)

It's recommended to use a Python virtual environment to isolate dependencies:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Quick Install

Without a virtual environment:
```bash
pip install -r requirements.txt
```

> **Note:** The script can run without these dependencies, but features like configuration file support (PyYAML) and image metadata reading (Pillow) will be unavailable.

## Quick Start

### Preview changes (dry-run mode)
```bash
python3 organize_profiles.py ./profiles
```

### Apply changes
```bash
python3 organize_profiles.py ./profiles --execute
```

### Interactive mode (for multi-printer profiles)
```bash
python3 organize_profiles.py ./profiles --interactive
```

## What It Does

- **Copies** files to `organized-profiles/` (original `profiles/` stays unchanged)
- **Standardizes** filenames to: `Printer Name - Paper Brand - Paper Type [N].icc`
- **Organizes** into folders: `organized-profiles/Printer/Brand/filename`
- **Normalizes** brand names (`cifa` → `Canson`, `HFA` → `Hahnemuehle`, etc.)
- **Detects** and removes duplicate PDFs via SHA-256 hashing
- **Handles** multi-printer profiles interactively or via preferences

## Configuration

The organizer uses an optional `config.yaml` file for:

1. **Printer Name Mappings** - Consolidate aliases to canonical names
   ```yaml
   printer_names:
     Canon Pixma PRO-100:
       - PRO-100
       - Pro-100
       - CanPro-100
       - pixmapro100
   ```

2. **Brand Name Mappings** - Normalize paper brand variations
   ```yaml
   brand_name_mappings:
     Canson:
       - cifa
       - CIFA
       - canson
   ```

3. **Paper Brands** - List of recognized brands
   ```yaml
   paper_brands:
     - Moab
     - Canson
     - Hahnemuehle
   ```

4. **Printer Remappings** - Remap profiles to a different printer
   ```yaml
   printer_remappings:
     "Epson SureColor P700": "Epson SureColor P900"
   ```

### Fallback Behavior

If `config.yaml` is missing or PyYAML isn't installed, the organizer automatically uses built-in defaults. PyYAML is included in `requirements.txt`, so install it via:
```bash
pip install -r requirements.txt
```

## Command-Line Options

```bash
# View help
python3 organize_profiles.py --help

# Dry-run preview
python3 organize_profiles.py ./profiles

# Execute changes
python3 organize_profiles.py ./profiles --execute

# Specify custom output directory
python3 organize_profiles.py ./profiles --output-dir ./my-organized-profiles --execute

# Interactive mode
python3 organize_profiles.py ./profiles --interactive

# Detailed output
python3 organize_profiles.py ./profiles --detailed

# Only organize profiles (skip PDFs)
python3 organize_profiles.py ./profiles --profiles-only --execute

# Only organize PDFs (skip profiles)
python3 organize_profiles.py ./profiles --pdfs-only --execute

# Suppress output
python3 organize_profiles.py ./profiles --quiet

# Copy to system ICC profile directory (prompts if available)
python3 organize_profiles.py ./profiles --execute --system-profiles

# Skip the system profile prompt
python3 organize_profiles.py ./profiles --execute --no-system-profiles-prompt
```

## Multi-Printer Profile Handling

Some profiles work with multiple printers (e.g., `MOAB Anasazi Canvas Matte P7570-P9570 ECM.icc`).

### How it works:

1. First time seeing a combo, you're prompted to choose a printer
2. Your choice is saved as a global rule in `.profile_preferences.json`
3. Future files with the same combo use your choice automatically

Example `.profile_preferences.json`:
```json
{
  "P7570-P9570": "Epson SureColor P7570",
  "P900-P950": "Epson SureColor P900"
}
```

## Output Structure

```
organized-profiles/
├── Canon Pixma PRO-100/
│   ├── Canson/
│   │   ├── Canon Pixma PRO-100 - Canson - aqua240.icc
│   │   └── ...
│   └── Moab/
│       ├── Canon Pixma PRO-100 - Moab - Anasazi Canvas.icc
│       └── ...
├── Epson SureColor P900/
│   ├── Canson/
│   └── Moab/
└── PDFs/
    ├── Canon Pixma PRO-100/
    ├── Epson SureColor P900/
    └── ...
```

Your original `profiles/` directory remains unchanged.

## System ICC Profile Directory Support

After organizing profiles, you can automatically copy them to your system's ICC profile directory, making them available to all applications.

### macOS - Choose Your Installation Scope

On macOS, you have two options:

**Option 1: System Directory** (requires admin)
- Path: `/Library/ColorSync/Profiles`
- Profiles available to all users on the computer
- Requires `sudo` or admin password
- Recommended for shared computers

**Option 2: User Directory** (no admin needed)
- Path: `~/Library/ColorSync/Profiles`
- Profiles available only to your user account
- No admin privileges required
- Recommended for personal use

#### macOS Usage:

```bash
# Normal flow - prompts you to choose system or user directory
python3 organize_profiles.py ./profiles --execute

# Output will show:
# ICC Profile Directory Options
# 1. System Directory (requires admin)
#    Path: /Library/ColorSync/Profiles
# 2. User Directory (no admin needed)
#    Path: ~/Library/ColorSync/Profiles
# Choose directory (1/2) or 'skip':
```

If you choose the system directory and don't have permission, the program will suggest:
```bash
sudo python3 organize_profiles.py ./profiles --execute --system-profiles
```

#### macOS: Set Ownership (Optional One-Time Setup)

To avoid needing `sudo` every time, you can change directory ownership:

```bash
# Change system color profiles directory to your user
sudo chown -R $(whoami) /Library/ColorSync/Profiles

# Verify ownership changed
ls -ld /Library/ColorSync/Profiles
```

After this, you can copy profiles without `sudo`.

### Windows - Administrator Required

On Windows, the system ICC profile directory requires administrator privileges:

**System Directory Path:** `C:\Windows\System32\spool\drivers\color`

#### Windows Usage:

```bash
# Without admin - will error with clear instructions
python3 organize_profiles.py ./profiles --execute --system-profiles

# Output will show:
# Elevated Privileges Required
# ERROR: Cannot write to Windows system ICC profile directory
# Path: C:\Windows\System32\spool\drivers\color
# This directory requires Administrator privileges.
# To fix this, please:
#   1. Open Command Prompt or PowerShell as Administrator
#   2. Run the program again with the --system-profiles flag
```

#### Windows: Run with Admin Privileges

1. **Open Command Prompt or PowerShell as Administrator:**
   - Press `Win + X` and select "Command Prompt (Admin)" or "PowerShell (Admin)"
   - Or: Right-click Command Prompt/PowerShell → "Run as administrator"

2. **Run the script:**
   ```bash
   python organize_profiles.py ./profiles --execute --system-profiles
   ```

3. **Note:** Profiles are copied to a flat structure (no subdirectories) as required by Windows.

### Command-Line Flags for System Profiles

- `--system-profiles` - Automatically copy to system ICC directory without prompting
- `--no-system-profiles-prompt` - Skip the system profile prompt entirely
- Default behavior (no flags) - Prompts if system directory is accessible

### Profile Directory Organization

The programs respects each OS's requirements:

**macOS:** Preserves your organized folder structure
```
~/Library/ColorSync/Profiles/
├── Canon Pixma PRO-100/
│   ├── Canson/
│   │   ├── Canon Pixma PRO-100 - Canson - aqua240.icc
│   │   └── ...
│   └── Moab/
└── Epson P900/
    └── ...
```

**Windows:** Uses flat structure (no subdirectories)
```
C:\Windows\System32\spool\drivers\color\
├── Canon Pixma PRO-100 - Canson - aqua240.icc
├── Canon Pixma PRO-100 - Moab - Anasazi Canvas.icc
├── Epson P900 - Moab - Entrada Rag.icc
└── ...
```

## Features

✅ **Smart Parsing** - Auto-detects and parses profiles from various manufacturers
✅ **Duplicate Handling** - SHA-256 hash-based PDF duplicate detection
✅ **Multi-Printer Support** - Interactive or rule-based handling
✅ **System Profile Installation** - Copy organized profiles to system ICC directories (macOS & Windows)
✅ **Safe Operations** - Dry-run by default, no modifications without `--execute`
✅ **Flexible Configuration** - Optional YAML config with sensible defaults
✅ **Detailed Logging** - All operations logged to `profile_organizer.log`

## Troubleshooting

**"Could not parse" warnings:**
- Some files may not be automatically recognized
- Check `profile_organizer.log` for details

**Multi-printer files keep prompting:**
- Verify `.profile_preferences.json` exists and contains the rule
- Try deleting preference files and recreating rules

**Want to change a printer choice:**
- Edit `.profile_preferences.json` directly
- Or delete the file and rerun with `--interactive`

### System Profile Directory Issues

**macOS: "No write permission" when choosing system directory:**

- The system directory `/Library/ColorSync/Profiles` requires admin access
- Choose option 2 (User Directory) instead, which doesn't require admin
- Or run with `sudo`: `sudo python3 organize_profiles.py ./profiles --execute --system-profiles`
- One-time setup to avoid sudo: `sudo chown -R $(whoami) /Library/ColorSync/Profiles`

**Windows: "Elevated Privileges Required" error:**

- Windows requires administrator privileges to write to the system profile directory
- Right-click Command Prompt/PowerShell → "Run as administrator"
- Then run: `python organize_profiles.py ./profiles --execute --system-profiles`

**Profiles aren't showing up in applications after copying:**

- macOS: Restart the application or restart your computer
- Windows: Some applications cache profiles on startup; restart them
- Try logging out and back in (macOS) or restarting (Windows) for guaranteed refresh

**Permission denied when copying to user directory (macOS):**

- Ensure the `~/Library/ColorSync` directory exists and you own it
- The script will create it automatically if it doesn't exist
- If issues persist, create it manually: `mkdir -p ~/Library/ColorSync/Profiles`

## Logging

All operations are logged to `profile_organizer.log` with timestamps and detailed information.
