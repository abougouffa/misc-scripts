import os, re, shutil, argparse, datetime
from PIL import Image, ExifTags
import pillow_heif

YMD_FILENAME_PATTERNS = (
    r"^((IMG|MOV|VID|PANO)[_-])?(?P<year>\d{4})[_-](?P<month>\d{2})[_-](?P<day>\d{2}).*\.\w+$",
    r"^((IMG|MOV|VID|PANO)[_-])?(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2}).*\.\w+$",
)

DMY_FILENAME_PATTERNS = (
    r"^((IMG|MOV|VID|PANO)[_-])?(?P<day>\d{2})[_-](?P<month>\d{2})[_-](?P<year>\d{4}).*\.\w+$",
    r"^((IMG|MOV|VID|PANO)[_-])?(?P<day>\d{2})(?P<month>\d{2})(?P<year>\d{4}).*\.\w+$",
)

MIN_YEAR = 2000


def validate_date(y, m, d):
    if int(y) >= MIN_YEAR:
        try:
            _ = datetime.datetime(year=int(y), month=int(m), day=int(d))
            return True
        except ValueError:
            pass
    return False


def date_from_pattern(pattern, filename):
    if match := re.match(pattern, filename):
        year, month, day = match.group("year"), match.group("month"), match.group("day")
        if validate_date(year, month, day):
            return f"{year}-{month}-{day}"
    return None


def get_dir_for_file_from_patterns(filename: str) -> None | str:
    for pattern_index, pattern in enumerate(YMD_FILENAME_PATTERNS):
        if dirname := date_from_pattern(pattern, filename):
            return dirname
        elif dirname := date_from_pattern(DMY_FILENAME_PATTERNS[pattern_index], filename):
            return dirname
    return None


def get_dir_for_file_from_exif(filename: str) -> None | str:
    try:
        img = Image.open(filename)
        if datetime := img.getexif().get(ExifTags.Base.DateTime):
            if match := re.match(r'^(?P<year>\d{4}):(?P<month>\d{2}):(?P<day>\d{2})', datetime):
                return f"{match.group("year")}-{match.group("month")}-{match.group("day")}"
        img.close()
    except Exception:
        pass
    return None


def main():
    # Add support for HEIF pictures
    pillow_heif.register_heif_opener()

    # Prepare the command line arguments parser
    parser = argparse.ArgumentParser(description="Classify photos in directories based on the file name patterns or the Exif metadata")
    parser.add_argument("--input", action="store", dest="input_dir")
    parser.add_argument("--output", action="store", dest="output_dir")
    parser.add_argument("--action", action="store", dest="action", default="move")
    # --mode=[auto|pattern|metadata]
    parser.add_argument("--mode", action="store", dest="mode", default="auto")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir if args.output_dir else args.input_dir
    action = args.action
    mode = args.mode

    # Get a list of files in the input directory
    files = os.listdir(args.input_dir)

    for file in files:
        full_filename = f"{input_dir}/{file}"
        target_dir = None
        if (outdir := get_dir_for_file_from_patterns(file)) and mode in ("auto", "pattern"):
            target_dir = f"{output_dir}/{outdir}"
        elif (outdir := get_dir_for_file_from_exif(full_filename)) and mode in ("auto", "metadata"):
            target_dir = f"{output_dir}/{outdir}"

        if target_dir:
            print(f"Moving {file} to {target_dir}")
            if not os.path.isdir(target_dir):
                os.mkdir(target_dir)
                pass
            if action == "copy":
                shutil.copy(f"{full_filename}", target_dir)
            elif action == "move":
                shutil.move(f"{full_filename}", target_dir)
        else:
            print(f"WARN: Cannot determine the date for {file}")


main()
