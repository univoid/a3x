import base64

def decode_base64(data):
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += b'='* (4 - missing_padding)
    return base64.decodestring(data)

def convert(image):
    f = open(image)
    data = f.read()
    f.close()
    base64_encode_str = base64.b64encode(data)

    t = open("out.jpeg", "wb+")
    t.write(decode_base64(base64_encode_str))
    t.close()
    return base64_encode_str

if __name__ == "__main__":
    print convert("in.jpeg")
