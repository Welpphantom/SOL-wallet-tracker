def lamports_to_sol(lamports):
    return round(lamports / 1000000000, 2)


def handle_swap(swap_meta):
  pre_swap_meta = swap_meta['preTokenBalances']
  post_swap_meta = swap_meta['postTokenBalances']
  pre_sol_balance = swap_meta['preBalances'][0]
  post_sol_balance = swap_meta['postBalances'][0]
  sol_amount = lamports_to_sol(abs(pre_sol_balance-post_sol_balance))

  '''
  Returns
  Action: [New Buy, Buy, Sell, Sell all]
  Token CA: CA
  Token Amount
  SOL Amount
  '''
  token_ca = pre_swap_meta[0]['mint']

  if len(pre_swap_meta) == 1:
    action = "New Buy"
    token_amount = post_swap_meta[0]['uiTokenAmount']['uiAmount']

    return action, token_ca, token_amount, sol_amount
  else:
    # its a rebuy or a sell
    pre_token_balance = pre_swap_meta[0]['uiTokenAmount']['uiAmount']
    post_token_balance = post_swap_meta[0]['uiTokenAmount']['uiAmount']
    if post_token_balance == None:
      action = "Sell all"
      token_amount = pre_token_balance
    elif pre_token_balance == None:
      # Rebuy after sell all
      action = "Re-buy"
      token_amount = post_token_balance
    elif post_token_balance < pre_token_balance:
      action = "Partial-Sell"
      token_amount = pre_token_balance - post_token_balance
    else:
      action = "Buy"
      token_amount = post_token_balance - pre_token_balance
    return action, token_ca, token_amount, sol_amount