#!/usr/bin/env python3
"""
Update ICC Profile Descriptions

This script scans organized-profiles directory and updates the description tag
in each ICC profile to match the profile's filename.
"""

import struct
from pathlib import Path
from typing import Optional, Tuple
import logging


class ICCProfileUpdater:
    """Handle reading and updating ICC profile descriptions."""

    # ASCII signature at start of ICC files
    ICC_SIGNATURE = b'acsp'

    # Tag signature for description
    DESC_TAG = b'desc'

    def __init__(self, verbose: bool = True):
        """Initialize the updater."""
        self.verbose = verbose
        self.setup_logging()

    def setup_logging(self):
        """Setup logging."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('update_descriptions.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log(self, message: str, level: str = 'INFO'):
        """Log a message."""
        if self.verbose:
            print(message)
        getattr(self.logger, level.lower())(message)

    def read_icc_profile(self, file_path: Path) -> Optional[bytes]:
        """Read ICC profile file."""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            self.log(f"Error reading {file_path}: {e}", level='ERROR')
            return None

    def write_icc_profile(self, file_path: Path, data: bytes) -> bool:
        """Write ICC profile file."""
        try:
            with open(file_path, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            self.log(f"Error writing {file_path}: {e}", level='ERROR')
            return False

    def validate_header(self, data: bytes) -> bool:
        """Validate ICC profile header."""
        if len(data) < 128:
            return False

        try:
            # Check for ICC signature at offset 36
            signature = data[36:40]
            return signature == self.ICC_SIGNATURE
        except Exception:
            return False

    def find_tag(self, data: bytes, tag_sig: bytes) -> Optional[Tuple[int, int]]:
        """
        Find tag in ICC profile.

        Returns tuple of (offset, size) or None if not found.
        """
        # Parse tag table at offset 128
        if len(data) < 132:
            return None

        try:
            tag_count = struct.unpack('>I', data[128:132])[0]

            # Each tag entry is 12 bytes: signature (4) + offset (4) + size (4)
            for i in range(tag_count):
                entry_offset = 132 + (i * 12)

                if entry_offset + 12 > len(data):
                    break

                entry_sig = data[entry_offset:entry_offset + 4]
                tag_offset = struct.unpack('>I', data[entry_offset + 4:entry_offset + 8])[0]
                tag_size = struct.unpack('>I', data[entry_offset + 8:entry_offset + 12])[0]

                if entry_sig == tag_sig:
                    return (tag_offset, tag_size)

            return None
        except Exception:
            return None

    def update_description_tag(self, data: bytes, new_description: str) -> Optional[bytes]:
        """
        Update the description tag in an ICC profile.

        The desc tag structure:
        - Bytes 0-3: Tag signature ('desc')
        - Bytes 4-7: Reserved (0)
        - Bytes 8-11: ASCII description length (including null terminator)
        - Bytes 12+: ASCII description
        """
        try:
            # Find existing desc tag
            tag_info = self.find_tag(data, self.DESC_TAG)

            if not tag_info:
                self.log("  Warning: No desc tag found, cannot update", level='WARNING')
                return None

            old_offset, old_size = tag_info

            # Create new desc tag data
            # Limit description to ASCII, max 255 chars
            desc_ascii = new_description.encode('ascii', errors='replace')[:255]

            # Create the desc tag structure
            desc_data = self.DESC_TAG  # 4 bytes: 'desc'
            desc_data += b'\x00\x00\x00\x00'  # 4 bytes: reserved

            desc_length = len(desc_ascii) + 1  # +1 for null terminator
            desc_data += struct.pack('>I', desc_length)  # 4 bytes: length
            desc_data += desc_ascii  # description
            desc_data += b'\x00'  # null terminator

            # Pad to multiple of 4 bytes (ICC requirement)
            padding = (4 - (len(desc_data) % 4)) % 4
            desc_data += b'\x00' * padding

            new_size = len(desc_data)

            # If new data is same size or smaller than old, we can safely replace
            if new_size <= old_size:
                # Pad the new data to match old size
                if new_size < old_size:
                    desc_data += b'\x00' * (old_size - new_size)

                # Simple replacement
                new_data = data[:old_offset] + desc_data + data[old_offset + old_size:]
                return new_data

            else:
                # New description is too long to fit in-place
                # For now, truncate to fit
                self.log(f"  Warning: Description too long, truncating", level='WARNING')

                # Truncate the description to fit
                max_desc_len = old_size - 12  # 12 bytes for header, rest for description
                if max_desc_len <= 0:
                    return None

                desc_ascii = new_description.encode('ascii', errors='replace')[:max_desc_len - 1]

                desc_data = self.DESC_TAG
                desc_data += b'\x00\x00\x00\x00'
                desc_length = len(desc_ascii) + 1
                desc_data += struct.pack('>I', desc_length)
                desc_data += desc_ascii
                desc_data += b'\x00'

                # Pad to old size
                padding = old_size - len(desc_data)
                if padding > 0:
                    desc_data += b'\x00' * padding

                new_data = data[:old_offset] + desc_data + data[old_offset + old_size:]
                return new_data

        except Exception as e:
            self.log(f"Error updating description tag: {e}", level='ERROR')
            return None

    def process_profile(self, file_path: Path) -> bool:
        """
        Process a single ICC profile file.

        Returns True if successful, False otherwise.
        """
        # Get the filename without extension as the new description
        new_description = file_path.stem

        # Read the profile
        profile_data = self.read_icc_profile(file_path)
        if not profile_data:
            return False

        # Validate header
        if not self.validate_header(profile_data):
            self.log(f"  Error: Invalid ICC profile header", level='ERROR')
            return False

        # Update description
        updated_data = self.update_description_tag(profile_data, new_description)
        if not updated_data:
            return False

        # Write back
        if self.write_icc_profile(file_path, updated_data):
            self.log(f"  ✓ Updated: {file_path.name}")
            return True

        return False

    def process_directory(self, directory: Path) -> Tuple[int, int]:
        """
        Process all ICC profiles in a directory recursively.

        Returns tuple of (processed, successful).
        """
        self.log("=" * 60)
        self.log("Starting ICC Profile Description Update")
        self.log(f"Directory: {directory}")
        self.log("=" * 60)

        # Find all ICC files
        icc_files = list(directory.rglob('*.icc'))
        icm_files = list(directory.rglob('*.icm'))

        # Filter out macOS resource forks
        icc_files = [f for f in icc_files if '._' not in f.name]
        icm_files = [f for f in icm_files if '._' not in f.name]

        all_files = icc_files + icm_files

        self.log(f"\nFound {len(all_files)} profile files")
        self.log(f"  ICC: {len(icc_files)} files")
        self.log(f"  ICM: {len(icm_files)} files")
        self.log("")

        processed = 0
        successful = 0

        for file_path in sorted(all_files):
            processed += 1
            if self.process_profile(file_path):
                successful += 1

        # Print summary
        self.log("\n" + "=" * 60)
        self.log("SUMMARY")
        self.log("=" * 60)
        self.log(f"Total files processed: {processed}")
        self.log(f"Successfully updated: {successful}")
        self.log(f"Failed: {processed - successful}")
        self.log("=" * 60)

        return processed, successful


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Update ICC profile descriptions to match filenames'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='./organized-profiles',
        help='Directory containing ICC profiles (default: ./organized-profiles)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output'
    )

    args = parser.parse_args()

    directory = Path(args.directory).resolve()

    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        return 1

    updater = ICCProfileUpdater(verbose=not args.quiet)
    processed, successful = updater.process_directory(directory)

    return 0 if successful == processed else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
