from hoot import Hoot
from os import listdir
from os.path import isfile, join

examples = [f for f in listdir("examples")  # grab all hoot files
            if isfile(join("examples", f)) if '.hoot' in f]

for example in examples:
    location = f"examples/{example}"
    print(f"\nRunning {location}..")
    exit_code = Hoot().run_file(location)
    if exit_code != 0:
        print(f"Error running {example} - code: {exit_code}")
        quit()

print("\nIntegration tests passed!")
