import requests

from breadcrumbcore.utils.utils import is_ascii

url = 'http://text-processing.com/api/sentiment/'


def analyse_text(text_list):
    if isinstance(text_list, str):
        text_list = [text_list]

    neg = 0.0
    neutral = 0.0
    pos = 0.0
    label = None

    counter = 0
    for text in text_list:
        if is_ascii(text):
            text = text.strip()
            data = 'text={}'.format(text)
            response = requests.post(url=url, data=data)
            if response:
                try:
                    out = response.json()
                    out_neg = float(out["probability"]["neg"])
                    out_neutral = float(out["probability"]["neutral"])
                    out_pos = float(out["probability"]["pos"])

                    neg += out_neg
                    neutral += out_neutral
                    pos += out_pos
                    counter += 1
                except Exception:
                    pass

    if counter > 0:
        neg /= counter
        neutral /= counter
        pos /= counter

    if neg >= neutral and neg >= pos:
        label = "neg"
    elif neutral >= neg and neutral >= pos:
        label = "neutral"
    elif pos >= neg and pos >= neutral:
        label = "pos"

    return {
        "probability": {
            "neg": neg,
            "neutral": neutral,
            "pos": pos
        },
        "label": label
    }
if __name__ == "__main__":
    text = "i hate my boss, wish he would just die"
    print analyse_text(text)