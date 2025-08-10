PROGRESS_BAR_WIDTH = 12

def progress_bar(curr: float, threshold: float, width: int = PROGRESS_BAR_WIDTH) -> str:
    if threshold <= 0:
        return "[" + " " * width + "]"
    ratio = max(0.0, min(1.0, curr / threshold))
    filled = int(round(ratio * width))
    return "[" + ("#" * filled).ljust(width) + "]"

