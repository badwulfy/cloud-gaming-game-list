def clean_string(input_str: str) -> str:
    """Format a string by removing invisible caracters and trailing spaces

    Args:
        input_str (str): input string

    Returns:
        str: trimed and cleaned string
    """
    return ''.join(c for c in input_str if c.isprintable()).strip(" ")