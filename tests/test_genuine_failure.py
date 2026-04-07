def calculate_discount(price, percent):
    return price - (price * percent / 100)

def test_discount_calculation():
    result = calculate_discount(100, 10)
    assert result == 80  # wrong — correct answer is 90, so this always fails
