import random
import string

def generate_order_number():
    letters = string.ascii_uppercase
    digits = string.digits

    first_char = random.choice(letters)
    remaining_chars = ''.join(random.choices(letters + digits, k=9))

    return first_char + remaining_chars