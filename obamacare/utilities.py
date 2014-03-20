"""
Function takes a string and cleans it by performing the following:
-First, it strips the string to remove excess whitespace
-next it removes all characters in 'remove' from the string
    except for those in 'exclude'
"""
default_remove = [';', ')', '(']
def clean(to_clean, remove=default_remove, exclude=[]):
    remove = [i for i in remove if i not in exclude]

    cleaned = to_clean.strip()
    for i in remove:
        cleaned = cleaned.replace(i, "")

    return cleaned
