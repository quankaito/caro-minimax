import tkinter as tk
from tkinter import messagebox
import random
# Import statement moved inside the back_to_menu method to avoid circular import

# --- Constants ---
DEFAULT_WIDTH = 700 # Chiều rộng mặc định của cửa sổ
DEFAULT_HEIGHT = 700 # Chiều cao mặc định của cửa sổ

BG_COLOR = "#F5F5DC" # Beige background color
LINE_COLOR = "#8B4513"  # Dark Brown line color
CIRC_COLOR = "#006400"  # Dark Green circle (O) color
CROSS_COLOR = "#8B0000" # Dark Red cross (X) color

WIN_LINE_COLOR = "#F5A742"  # Màu đường thắng (màu cam)
WIN_LINE_WIDTH = 15  # Độ dày của đường thắng 
WIN_LINE_LENGTH = 1.2  # Tỷ lệ nhân để kéo dài đường kẻ

class Board:
    def __init__(self, size):
        self.size = size
        self.board = self.make_empty_board()
        self.move_history = []

    def make_empty_board(self):
        return [[" "] * self.size for _ in range(self.size)]

    def is_empty(self):
        return all(cell == " " for row in self.board for cell in row)

    def is_in(self, y, x):
        return 0 <= y < self.size and 0 <= x < self.size

    def is_win(self):
        x_score = self.score_of_col('X')
        o_score = self.score_of_col('O')
        
        self.sum_sumcol_values(x_score)
        self.sum_sumcol_values(o_score)
        
        if 5 in x_score and x_score[5] == 1:
            return 'X won'
        elif 5 in o_score and o_score[5] == 1:
            return 'O won'
            
        if sum(x_score.values()) == x_score[-1] and sum(o_score.values()) == o_score[-1] or self.possible_moves() == []:
            return 'Draw'
            
        return 'Continue playing'

    def march(self, y, x, dy, dx, length):
        yf = y + length * dy 
        xf = x + length * dx
        while not self.is_in(yf, xf):
            yf -= dy
            xf -= dx
        return yf, xf

    @staticmethod
    def score_ready(scorecol):
        sumcol = {i: {} for i in range(-1, 6)}
        for key in scorecol:
            for score in scorecol[key]:
                if key in sumcol[score]:
                    sumcol[score][key] += 1
                else:
                    sumcol[score][key] = 1
        return sumcol

    @staticmethod
    def sum_sumcol_values(sumcol):
        for key in sumcol:
            if key == 5:
                sumcol[5] = int(1 in sumcol[5].values())
            else:
                sumcol[key] = sum(sumcol[key].values())

    @staticmethod
    def score_of_list(lis, col):
        blank = lis.count(' ')
        filled = lis.count(col)
        if blank + filled < 5:
            return -1
        elif blank == 5:
            return 0
        else:
            return filled

    def row_to_list(self, y, x, dy, dx, yf, xf):
        row = []
        while y != yf + dy or x != xf + dx:
            row.append(self.board[y][x])
            y += dy
            x += dx
        return row

    def score_of_row(self, cordi, dy, dx, cordf, col):
        colscores = []
        y, x = cordi
        yf, xf = cordf
        row = self.row_to_list(y, x, dy, dx, yf, xf)
        for start in range(len(row) - 4):
            score = self.score_of_list(row[start:start + 5], col)
            colscores.append(score)
        return colscores

    def score_of_col(self, col):
        f = self.size
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}
        for start in range(self.size):
            scores[(0, 1)].extend(self.score_of_row((start, 0), 0, 1, (start, f - 1), col))
            scores[(1, 0)].extend(self.score_of_row((0, start), 1, 0, (f - 1, start), col))
            scores[(1, 1)].extend(self.score_of_row((start, 0), 1, 1, (f - 1, f - 1 - start), col))
            scores[(-1, 1)].extend(self.score_of_row((start, 0), -1, 1, (0, start), col))
            
            if start + 1 < self.size:
                scores[(1, 1)].extend(self.score_of_row((0, start + 1), 1, 1, (f - 2 - start, f - 1), col))
                scores[(-1, 1)].extend(self.score_of_row((f - 1, start + 1), -1, 1, (start + 1, f - 1), col))
                
        return self.score_ready(scores)

    def score_of_col_one(self, col, y, x):
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}
        
        scores[(0, 1)].extend(self.score_of_row(self.march(y, x, 0, -1, 4), 0, 1, self.march(y, x, 0, 1, 4), col))
        scores[(1, 0)].extend(self.score_of_row(self.march(y, x, -1, 0, 4), 1, 0, self.march(y, x, 1, 0, 4), col))
        scores[(1, 1)].extend(self.score_of_row(self.march(y, x, -1, -1, 4), 1, 1, self.march(y, x, 1, 1, 4), col))
        scores[(-1, 1)].extend(self.score_of_row(self.march(y, x, -1, 1, 4), 1, -1, self.march(y, x, 1, -1, 4), col))
        
        return self.score_ready(scores)

    def possible_moves(self):
        taken = [(i, j) for i in range(self.size) for j in range(self.size) if self.board[i][j] != ' ']
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (-1, 1), (1, -1)]
        cord = {}
        
        for direction in directions:
            dy, dx = direction
            for coord in taken:
                y, x = coord
                for length in [1, 2, 3, 4]:
                    move = self.march(y, x, dy, dx, length)
                    if move not in taken and move not in cord:
                        cord[move] = False
        return cord

    @staticmethod
    def TF34score(score3, score4):
        for key4 in score4:
            if score4[key4] >= 1:
                for key3 in score3:
                    if key3 != key4 and score3[key3] >= 2:
                        return True
        return False

    def stupid_score(self, col, anticol, y, x):
        M = 1000
        res, adv, dis = 0, 0, 0
        
        self.board[y][x] = col
        sumcol = self.score_of_col_one(col, y, x)       
        a = self.winning_situation(sumcol)
        adv += a * M
        self.sum_sumcol_values(sumcol)
        adv += sumcol[-1] + sumcol[1] + 4 * sumcol[2] + 8 * sumcol[3] + 16 * sumcol[4]
        
        self.board[y][x] = anticol
        sumanticol = self.score_of_col_one(anticol, y, x)  
        d = self.winning_situation(sumanticol)
        dis += d * (M - 100)
        self.sum_sumcol_values(sumanticol)
        dis += sumanticol[-1] + sumanticol[1] + 4 * sumanticol[2] + 8 * sumanticol[3] + 16 * sumanticol[4]

        res = adv + dis
        
        self.board[y][x] = ' '
        return res

    @staticmethod
    def winning_situation(sumcol):
        if 1 in sumcol[5].values():
            return 5
        elif len(sumcol[4]) >= 2 or (len(sumcol[4]) >= 1 and max(sumcol[4].values()) >= 2):
            return 4
        elif Board.TF34score(sumcol[3], sumcol[4]):
            return 4
        else:
            score3 = sorted(sumcol[3].values(), reverse=True)
            if len(score3) >= 2 and score3[0] >= score3[1] >= 2:
                return 3
        return 0

    def best_move(self, col):
        anticol = 'O' if col == 'X' else 'X'
        
        if self.is_empty():
            return (int((self.size) * random.random()), int((self.size) * random.random()))
        
        moves = self.possible_moves()
        best_move = None
        max_score = float('-inf')

        for move in moves:
            y, x = move
            score = self.stupid_score(col, anticol, y, x)
            if score > max_score:
                max_score = score
                best_move = move

        return best_move

class Game(tk.Tk):
    def __init__(self, size=15, gamemode='ai'):
        super().__init__()
        self.title("TRÍ TUỆ NHÂN TẠO-NHÓM 2")
        self.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT + 100}")
        self.canvas = tk.Canvas(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, bg=BG_COLOR)
        self.canvas.pack()

        self.size = size
        self.sqsize = DEFAULT_WIDTH // int(self.size)  # Kích thước mỗi ô vuông trên bảng
        self.radius = self.sqsize // 4  # Bán kính của dấu tròn (O)
        self.offset = self.sqsize // 4  # Khoảng cách bù trừ cho việc vẽ dấu
        self.line_width = self.offset // 2  # Độ dày của các đường kẻ
        self.circ_width = self.offset // 2  # Độ dày của đường kẻ dấu tròn (O)
        self.cross_width = self.offset // 2  # Độ dày của đường kẻ dấu chéo (X)

        self.board = Board(self.size)  # Tạo bảng chơi với kích thước được chỉ định
        self.player = 1  # Người chơi bắt đầu
        self.gamemode = gamemode  # Chế độ chơi (Player vs Player or Player vs A.I)
        self.running = True  # Trạng thái trò chơi đang chạy
        self.ai_thinking = False  # Trạng thái AI đang suy nghĩ
        self.canvas.bind("<Button-1>", self.handle_click)  # Ràng buộc sự kiện click chuột trên canvas

        # Reset button 
        self.reset_button = tk.Button(self, text="Chơi lại", command=self.reset, font=("Manrope", 16, "bold"), padx=20, pady=10)
        self.reset_button.pack(side=tk.LEFT, padx=20, pady=20)
        # Back button 
        self.back_button = tk.Button(self, text="Trở về", command=self.back, font=("Manrope", 16, "bold"), padx=20, pady=10)
        self.back_button.pack(side=tk.RIGHT, padx=20, pady=20)

        # Status label
        self.status_label = tk.Label(self, text="", font=("Manrope", 20))
        self.status_label.pack(pady=10)

        # Call the show_lines() method at the end of the __init__ method
        self.show_lines()  # Vẽ lưới bàn cờ

    def handle_click(self, event):
        if not self.running or self.ai_thinking:
            return

        x, y = event.x, event.y
        row, col = y // self.sqsize, x // self.sqsize

        if self.board.is_in(row, col) and self.board.board[row][col] == " ":
            self.make_move(row, col, 'X')
            if self.check_game_end():
                return

            if self.gamemode == 'ai':
                self.ai_thinking = True
                self.after(100, self.ai_move)

    def create_widgets(self):
        for i in range(self.board.size):
            for j in range(self.board.size):
                b = tk.Button(self.master, text=' ', width=4, height=2,
                              command=lambda row=i, col=j: self.click(row, col))
                b.grid(row=i, column=j, padx=5, pady=5)
                self.buttons[i][j] = b

        # Add a "Back" button to return to the main menu
        self.back_button = tk.Button(self.master, text="Back", command=self.back_to_menu, font=("Helvetica", 14, "bold"), fg="#FFFFFF", bg="#4CAF50", padx=10, pady=5)
        self.back_button.grid(row=self.board.size, column=0, columnspan=self.board.size, pady=10)

    def ai_move(self):
        ai_row, ai_col = self.board.best_move('O')
        self.make_move(ai_row, ai_col, 'O')
        self.check_game_end()
        self.ai_thinking = False

    def make_move(self, row, col, player):
        self.board.board[row][col] = player
        self.draw_move(row, col, player)
        self.board.move_history.append((row, col))

    def draw_move(self, row, col, player):
        x0 = col * self.sqsize + self.offset
        y0 = row * self.sqsize + self.offset
        x1 = (col + 1) * self.sqsize - self.offset
        y1 = (row + 1) * self.sqsize - self.offset

        if player == 'X':
            self.canvas.create_line(x0, y0, x1, y1, width=self.cross_width, fill=CROSS_COLOR)
            self.canvas.create_line(x0, y1, x1, y0, width=self.cross_width, fill=CROSS_COLOR)
        elif player == 'O':
            self.canvas.create_oval(x0, y0, x1, y1, width=self.circ_width, outline=CIRC_COLOR)

    def check_game_end(self):
        game_res = self.board.is_win()
        if game_res in ["X won", "O won", "Draw"]:
            self.status_label.config(text=game_res)
            self.running = False
            return True
        return False

    def reset(self):
        self.board = Board(self.size)
        self.canvas.delete("all")
        self.show_lines()
        self.status_label.config(text="")
        self.running = True

    def show_lines(self):
        for i in range(self.size):
            self.canvas.create_line(0, i * self.sqsize, DEFAULT_WIDTH, i * self.sqsize, fill=LINE_COLOR, width=self.line_width)
            self.canvas.create_line(i * self.sqsize, 0, i * self.sqsize, DEFAULT_HEIGHT, fill=LINE_COLOR, width=self.line_width)

    def back(self):
        self.destroy()  # Đóng cửa sổ hiện tại
        from caro_menu import CaroUI  # Quay lại form menu
        root = tk.Tk()  # Tạo cửa sổ mới
        ui = CaroUI(root)  # Khởi tạo giao diện menu
        root.mainloop()  # Chạy vòng lặp chính của giao diện
        try:
            from caro_menu import CaroUI
            root = tk.Tk()
            ui = CaroUI(root)
            root.mainloop()
        except ImportError:
            messagebox.showerror("Error", "CaroUI module not found.")

def main():
    game = Game(size=15)
    game.mainloop()

if __name__ == "__main__":
    main()
