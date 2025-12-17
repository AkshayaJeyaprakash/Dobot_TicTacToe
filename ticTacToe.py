import math

def is_moves_left(board):
    for row in board:
        if '_' in row:
            return True
    return False


def evaluate(board):
    for row in board:
        if row[0] == row[1] == row[2] != '_':
            return 10 if row[0] == 'x' else -10

    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != '_':
            return 10 if board[0][col] == 'x' else -10

    if board[0][0] == board[1][1] == board[2][2] != '_':
        return 10 if board[0][0] == 'x' else -10
    if board[0][2] == board[1][1] == board[2][0] != '_':
        return 10 if board[0][2] == 'x' else -10
    return 0

def minimax(board, depth, is_maximizing):
    score = evaluate(board)
    if score == 10 or score == -10:
        return score
    if not is_moves_left(board):
        return 0

    if is_maximizing:
        best = -math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == '_':
                    board[i][j] = 'x'
                    best = max(best, minimax(board, depth + 1, False))
                    board[i][j] = '_'
        return best
    else:
        best = math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == '_':
                    board[i][j] = 'o'
                    best = min(best, minimax(board, depth + 1, True))
                    board[i][j] = '_'
        return best


def evaluate_next_move(board):
    best_val = -math.inf
    best_move = (-1, -1)

    for i in range(3):
        for j in range(3):
            if board[i][j] == '_':
                board[i][j] = 'x'
                move_val = minimax(board, 0, False)
                board[i][j] = '_'
                if move_val > best_val:
                    best_move = (i, j)
                    best_val = move_val

    return best_move


# ------------------ FOR TERMINAL PLAY ------------------

def print_board(board):
    print("\n".join([" | ".join(row) for row in board]))
    print()


def check_winner(board):
    val = evaluate(board)
    if val == 10:
        return "Robot wins!"
    elif val == -10:
        return "Human wins!"
    elif not is_moves_left(board):
        return "It's a draw!"
    return None


def main():
    print("Welcome to Tic Tac Toe!")
    print("Robot: X | Human: O\n")

    board = [['_', '_', '_'],
             ['_', '_', '_'],
             ['_', '_', '_']]

    robot_turn = False

    while True:
        print_board(board)
        winner = check_winner(board)
        if winner:
            print(winner)
            break

        if robot_turn:
            print("Robot is thinking...")
            i, j = evaluate_next_move(board)
            board[i][j] = 'x'
            robot_turn = False
        else:
            try:
                move = input("Enter your move (row col): ")
                i, j = map(int, move.strip().split())
                i, j = i - 1, j - 1
                if board[i][j] == '_':
                    board[i][j] = 'o'
                    robot_turn = True
                else:
                    print("Cell already taken. Try again.")
            except:
                print("Invalid input. Use format: row col (e.g. 2 3)")


if __name__ == "__main__":
    main()
