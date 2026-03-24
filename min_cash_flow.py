''' Idea
	1.	Always match: largest debtor with largest creditor
	2.	Settle as much as possible
	3.	Update balances
	4.	Repeat until all are 0
'''


def normalize_state(state):
    normalized = []
    for entry in state:
        person, amount = entry
        normalized.append([person, float(amount)])
    return normalized

def build_net_amounts(final_state, initial_state):
    net_amounts = []
    for i in range(len(final_state)):
        person = final_state[i][0]
        net_amount = final_state[i][1] - initial_state[i][1]
        net_amounts.append([person, net_amount])
    return net_amounts


def split_and_sort_balances(net_amounts):
    owes = [person for person in net_amounts if person[1] < 0]
    owes.sort(key=lambda x: x[1])  # Most negative first

    owed = [person for person in net_amounts if person[1] > 0]
    owed.sort(key=lambda x: x[1], reverse=True)  # Most positive first

    return owes, owed


def summarize_totals(owes, owed):
    sum_owes = 0
    for num in owes:
        sum_owes += num[1]

    sum_owed = 0
    for num in owed:
        sum_owed += -num[1]

    return sum_owes, sum_owed


def build_header_transactions(sum_owes, sum_owed):
    transactions = []
    if sum_owed != sum_owes:
        transactions.append(
            f"Warning: Total owed does not match total owes. Please check the input data.\n\nTotal Owed: ${sum_owed:.2f}, Total Owes: ${-sum_owes:.2f}\n"
        )
    else:
        transactions.append(f"Total Owed: ${sum_owed:.2f}, Total Owes: ${-sum_owes:.2f}\n")
    transactions.append("Transactions to settle debts:")
    return transactions


def settle_transactions(owes, owed, transactions):
    n_owes = len(owes)
    n_owed = len(owed)

    i = 0
    j = 0
    while i < n_owes:
        debtor, debt_amount = owes[i]
        debt_amount = -debt_amount

        while (j < n_owed) and (debt_amount > 0):
            creditor, credit_amount = owed[j]
            transfer_amount = min(debt_amount, credit_amount)

            transactions.append(f'{debtor} -> {creditor} ${transfer_amount:.2f}')

            owes[i][1] += transfer_amount
            owed[j][1] -= transfer_amount

            if owed[j][1] == 0:
                j += 1
            debt_amount = -owes[i][1]

        i += 1

    return transactions


def compute(final_state, initial_state):
    final_state = normalize_state(final_state)
    initial_state = normalize_state(initial_state)

    net_amounts = build_net_amounts(final_state, initial_state)
    owes, owed = split_and_sort_balances(net_amounts)
    sum_owes, sum_owed = summarize_totals(owes, owed)
    transactions = build_header_transactions(sum_owes, sum_owed)
    return settle_transactions(owes, owed, transactions)



if __name__ == "__main__":
    trasactions = compute([['chan', 12], ['daniel', 12.70], ['cheryl', 27.50], ['ben', 23.50], ['shi pei', 19],
                  ['kesh + ryan', 47], ['solaiy', 17], ['jonte', 13], ['Sean', 7.5]],
        [['chan', 20], ['daniel', 20], ['cheryl', 20], ['ben', 20], ['shi pei', 20], ['kesh + ryan', 20], ['solaiy', 20], ['jonte', 20], ['Sean', 20]])
    
    for t in trasactions:
        print(t)
