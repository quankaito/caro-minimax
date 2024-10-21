import copy
import random
import numpy as np
import tkinter as tk
from tkinter import messagebox
import time
from functools import lru_cache

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
        self.size = size # Kích thước bàn cờ (NxN)
        self.squares = np.zeros((size, size), dtype=int) # Khởi tạo bàn cờ với các ô vuông giá trị 0
        self.marked_sqrs = 0 # Số ô đã được đánh dấu
        self.max_item_win = 3 if size == 5 else 5 # Điều kiện thắng (3 liên tiếp cho 5x5, 5 liên tiếp cho các kích thước khác)
        self.winning_line = None # Để lưu đường thắng

    # Kiểm tra trạng thái kết thúc (thắng/thua) sau khi đánh một nước
    def final_state(self, marked_row, marked_col):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)] # Các hướng kiểm tra (dọc, ngang, chéo phải, chéo trái)
        player = self.squares[marked_row][marked_col]  # Người chơi hiện tại

        for dr, dc in directions: # Duyệt qua mỗi hướng để kiểm tra thắng
            count = 0 # Khởi tạo biến đếm số ô liên tiếp
            start = None
            for delta in range(-self.max_item_win + 1, self.max_item_win):  # Duyệt qua khoảng giá trị từ -max_item_win + 1 đến max_item_win
                r = marked_row + delta * dr  # Tính toán vị trí dọc
                c = marked_col + delta * dc  # Tính toán vị trí ngang
                if 0 <= r < self.size and 0 <= c < self.size:
                    if self.squares[r][c] == player:
                        if count == 0:
                            start = (r, c)
                        count += 1
                        if count == self.max_item_win:
                            self.winning_line = (start, (r, c))
                            return player
                    else:
                        count = 0
                        start = None
                else:
                    count = 0
                    start = None
        return 0

    # Đánh dấu ô tại vị trí `row`, `col` với giá trị `player`
    def mark_sqr(self, row, col, player):
        self.squares[row][col] = player # Đánh dấu ô với người chơi
        self.marked_sqrs += 1 # Tăng số ô đã đánh dấu

    def empty_sqr(self, row, col):
        return self.squares[row][col] == 0 # Tăng số ô đã đánh dấu

    def get_empty_sqrs(self):
        return [(r, c) for r in range(self.size) for c in range(self.size) if self.empty_sqr(r, c)] # Lấy danh sách các ô trống

    def is_full(self):
        return self.marked_sqrs == self.size * self.size # Kiểm tra bàn cờ có đầy không

    # Tính độ dài dây liên tiếp dài nhất của một người chơi trên bàn cờ
    def longest_sequence(self, player):
        longest = 0 # Độ dài lớn nhất của chuỗi
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)] # Các hướng có thể kiểm tra
        for row in range(self.size):
            for col in range(self.size):
                if self.squares[row][col] == player:
                    for dr, dc in directions:
                        count = 0
                        for delta in range(-self.max_item_win + 1, self.max_item_win):
                            r = row + delta * dr
                            c = col + delta * dc
                            if 0 <= r < self.size and 0 <= c < self.size and self.squares[r][c] == player:
                                count += 1
                                longest = max(longest, count)
                            else:
                                count = 0
        return longest

class AI:
    def __init__(self, player=2): # Số đại diện cho AI (thường là 2)
        self.player = player 
        self.opponent = 3 - player # Số đại diện cho đối thủ (thường là 1)
        self.max_time = 5  # Giới hạn thời gian suy nghĩ (giây)
        # Sử dụng bộ nhớ đệm để tối ưu hóa hàm evaluate_board
        self.evaluate_board = lru_cache(maxsize=10000)(self.evaluate_board) 
        self.transposition_table = {} # Bảng chuyển vị để lưu trữ các trạng thái đã đánh giá
        # opening_book cho các nước đi đầu tiên trên các kích thước bàn cờ khác nhau
        self.opening_book = {
            (5, 5): [(2, 2), (2, 3), (3, 2), (3, 3)],  # Các nước đi mở đầu cho bàn cờ 5x5
            (7, 7): [(3, 3), (3, 4), (4, 3), (4, 4)]   # Các nước đi mở đầu cho bàn cờ 7x7
        }

    def eval(self, main_board):
        start_time = time.time() # Bắt đầu đếm thời gian
        # Kiểm tra opening_book nếu ít hơn 2 nước đi đã được thực hiện
        if main_board.marked_sqrs < 2 and (main_board.size, main_board.size) in self.opening_book:
            return random.choice(self.opening_book[(main_board.size, main_board.size)])

        empty_sqrs = main_board.get_empty_sqrs()
        
        # Quick evaluation for early game (Đánh giá nhanh cho giai đoạn đầu trò chơi khi còn nhiều ô trống bàn cờ)
        if len(empty_sqrs) > main_board.size * main_board.size - 4:
            return self.quick_eval(main_board, empty_sqrs)

        # Check for immediate winning moves and blocks (Kiểm tra nước đi chiến thắng ngay lập tức và chặn đối thủ)
        for row, col in empty_sqrs:
            if self.is_winning_move(main_board, row, col, self.player):
                return (row, col)
        for row, col in empty_sqrs:
            if self.is_winning_move(main_board, row, col, self.opponent):
                return (row, col)

        # Check for open threes and other complex strategic positions (Kiểm tra các vị trí chiến lược phức tạp [ví dụ: tạo chuỗi ba mở])
        strategic_move = self.check_strategic_positions(main_board)
        if strategic_move:
            return strategic_move

        # Use iterative deepening within time limit (Sử dụng tìm kiếm sâu dần trong giới hạn thời gian còn lại)
        return self.iterative_deepening(main_board, 10, self.max_time - (time.time() - start_time))

    def quick_eval(self, board, empty_sqrs):
        # Đánh giá nhanh bằng cách chọn ô gần trung tâm nhất
        center = board.size // 2 # Tâm bàn cờ
        best_move = None
        best_score = -float('inf')

        for row, col in empty_sqrs:
            # Tính điểm dựa trên khoảng cách Manhattan đến trung tâm
            score = -(abs(row - center) + abs(col - center))  # Ưu tiên các nước gần tâm
            if score > best_score:
                best_score = score
                best_move = (row, col)

        return best_move

    def is_winning_move(self, board, row, col, player):
        # Kiểm tra xem nước đi có dẫn đến chiến thắng không
        temp_board = copy.deepcopy(board)
        temp_board.mark_sqr(row, col, player)
        return temp_board.final_state(row, col) == player  #Kiểm tra nếu là nước thắng

    def check_strategic_positions(self, board):
        for row in range(board.size):
            for col in range(board.size):
                if board.empty_sqr(row, col):
                    # Kiểm tra xem nước đi có tạo ra chuỗi ba mở cho AI không
                    if self.is_open_three(board, row, col, self.player):
                        return (row, col)
                    # Kiểm tra và chặn chuỗi ba mở của đối thủ
                    if self.is_open_three(board, row, col, self.opponent):
                        return (row, col)
        return None

    def is_open_three(self, board, row, col, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            line = self.get_line(board, row, col, dr, dc)
            if self.is_open_three_pattern(line, player):
                return True
        return False

    def is_open_three_pattern(self, line, player):
        # Mẫu chuỗi ba mở: 0XXX0 (với X là quân của người chơi)
        pattern = [0, player, player, player, 0]
        return pattern in [line[i:i+5] for i in range(len(line)-4)]

    def get_line(self, board, row, col, dr, dc):
        # Lấy một dòng các ô từ vị trí (row, col) theo hướng (dr, dc)
        line = []
        for i in range(-board.max_item_win + 1, board.max_item_win):
            r, c = row + i * dr, col + i * dc
            if 0 <= r < board.size and 0 <= c < board.size:
                line.append(board.squares[r][c])
            else:
                break
        return line

    def evaluate_board(self, board):
        score = 0
        if self.check_win(board, self.player):
            score += 10000
        if self.check_win(board, self.opponent):
            score -= 10000
        for row in range(board.size):
            for col in range(board.size):
                if board.squares[row][col] == self.player:
                    score += self.evaluate_position(board, row, col, self.player)
                elif board.squares[row][col] == self.opponent:
                    score -= self.evaluate_position(board, row, col, self.opponent)
        return score

    def evaluate_position(self, board, row, col, player):
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 0
            block_count = 0
            for delta in range(-3, 4):
                r = row + delta * dr
                c = col + delta * dc
                if 0 <= r < board.size and 0 <= c < board.size:
                    if board.squares[r][c] == player:
                        count += 1
                    elif board.squares[r][c] != 0:
                        block_count += 1
                        break
                else:
                    block_count += 1
                    break
            if block_count < 2:
                score += count ** 2
        return score

    def check_win(self, board, player):
        for row in range(board.size):
            for col in range(board.size):
                if board.squares[row][col] == player:
                    if board.final_state(row, col) == player:
                        return True
        return False

    def evaluate_sequences(self, board, player):
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for row in range(board.size):
            for col in range(board.size):
                for dr, dc in directions:
                    score += self.evaluate_direction(board, row, col, dr, dc, player)
        return score

    def evaluate_direction(self, board, row, col, dr, dc, player):
        score = 0
        max_win = board.max_item_win
        line = []
        for i in range(max_win):
            r, c = row + i * dr, col + i * dc
            if 0 <= r < board.size and 0 <= c < board.size:
                line.append(board.squares[r][c])
            else:
                break
        if len(line) >= max_win:
            score += self.score_window(line, player, max_win)
        return score

    def score_window(self, window, player, max_win):
        score = 0
        opponent = 3 - player
        
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(0)
        
        if opponent_count == max_win - 1 and empty_count == 1:
            score -= 2000  # Prioritize blocking opponent's winning move
        elif player_count == max_win - 1 and empty_count == 1:
            score += 1000
        elif opponent_count == max_win - 2 and empty_count == 2:
            score -= 500   
        elif player_count == max_win - 2 and empty_count == 2:
            score += 100
        elif player_count > 0 and opponent_count == 0:
            score += 10 * player_count
        elif opponent_count > 0 and player_count == 0:
            score -= 15 * opponent_count
        
        return score

    def evaluate_potential_advantages(self, board, player):
        score = 0
        opponent = 3 - player
        for row in range(board.size):
            for col in range(board.size):
                if board.squares[row][col] == 0:
                    score += self.evaluate_future_sequence(board, row, col, player)
                    score -= self.evaluate_future_sequence(board, row, col, opponent)
        return score

    def evaluate_future_sequence(self, board, row, col, player):
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            line = self.get_line(board, row, col, dr, dc)
            score += self.score_potential_sequence(line, player, board.max_item_win)
        return score

    def score_potential_sequence(self, line, player, max_win):
        score = 0
        opponent = 3 - player
        player_count = line.count(player)
        empty_count = line.count(0)
        
        if player_count == max_win - 2 and empty_count == 2:
            score += 50  # Potential future advantage
        elif player_count == max_win - 3 and empty_count == 3:
            score += 10  # Developing sequence
        
        return score

    def iterative_deepening(self, board, max_depth, max_time):
        best_move = None
        start_time = time.time()
        for depth in range(1, max_depth + 1):
            if time.time() - start_time > max_time:
                break
            score, move = self.minimax(board, depth, -float('inf'), float('inf'), True, start_time)
            if move:
                best_move = move
        return best_move

    def minimax(self, board, depth, alpha, beta, maximizing, start_time):
        # Điều kiện dừng: đạt độ sâu 0, bàn cờ đầy, hoặc hết thời gian
        if depth == 0 or board.is_full() or time.time() - start_time > self.max_time:
            return self.evaluate_board(board), None

        empty_sqrs = board.get_empty_sqrs()
        # Sắp xếp các nước đi theo thứ tự ưu tiên để cắt tỉa alpha-beta hiệu quả hơn
        empty_sqrs.sort(key=lambda move: self.move_ordering_score(board, move[0], move[1]), reverse=maximizing)

        if maximizing:
            max_eval = -float('inf')
            best_move = None
            for (row, col) in empty_sqrs:
                temp_board = copy.deepcopy(board)
                temp_board.mark_sqr(row, col, self.player)
                eval, _ = self.minimax(temp_board, depth - 1, alpha, beta, False, start_time)
                if eval > max_eval:
                    max_eval = eval
                    best_move = (row, col)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break # Cắt tỉa alpha
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            for (row, col) in empty_sqrs:
                temp_board = copy.deepcopy(board)
                temp_board.mark_sqr(row, col, self.opponent)
                eval, _ = self.minimax(temp_board, depth - 1, alpha, beta, True, start_time)
                if eval < min_eval:
                    min_eval = eval
                    best_move = (row, col)
                beta = min(beta, eval)
                if beta <= alpha:
                    break # Cắt tỉa beta
            return min_eval, best_move

    def move_ordering_score(self, board, row, col):
        score = 0
        center = board.size // 2
        # Ưu tiên các nước đi gần trung tâm
        score += 10 - (abs(row - center) + abs(col - center))
        
        # Prioritize moves that form or block potential advantages (Ưu tiên các nước đi tạo ra hoặc chặn các lợi thế tiềm năng)
        temp_board = copy.deepcopy(board)
        temp_board.mark_sqr(row, col, self.player)
        score += self.evaluate_potential_advantages(temp_board, self.player)
        
        temp_board = copy.deepcopy(board)
        temp_board.mark_sqr(row, col, self.opponent)
        score += self.evaluate_potential_advantages(temp_board, self.opponent)
        
        return score

class Game(tk.Tk):
    def __init__(self, size=5, gamemode='ai'):
        super().__init__()
        self.title("TRÍ TUỆ NHÂN TẠO-NHÓM 2") # Tiêu đề cửa sổ
        self.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT + 100}") # Kích thước cửa sổ
        self.canvas = tk.Canvas(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, bg=BG_COLOR) # Tạo canvas
        self.canvas.pack()

        self.size = size # Kích thước bàn cờ
        self.sqsize = DEFAULT_WIDTH // self.size # Kích thước mỗi ô vuông trên bảng
        self.radius = self.sqsize // 4 # Bán kính của dấu tròn (O)
        self.offset = self.sqsize // 4 # Khoảng cách bù trừ cho việc vẽ dấu
        self.line_width = self.offset // 2  # Độ dày của các đường kẻ
        self.circ_width = self.offset // 2 # Độ dày của đường kẻ dấu tròn (O)
        self.cross_width = self.offset // 2 # Độ dày của đường kẻ dấu chéo (X)
 
        self.board = Board(self.size) # Tạo bảng chơi với kích thước được chỉ định
        self.ai = AI() # Tạo đối tượng AI
        self.player = 1 # Người chơi bắt đầu
        self.gamemode = gamemode # Chế độ chơi (Player vs Player or Player vs A.I)
        self.running = True # Trạng thái trò chơi đang chạy
        self.ai_thinking = False # Trạng thái AI đang suy nghĩ
        self.show_lines() # Vẽ lưới bàn cờ
        self.canvas.bind("<Button-1>", self.handle_click) # Ràng buộc sự kiện click chuột trên canvas

        # Reset button 
        self.reset_button = tk.Button(self, text="Chơi lại", command=self.reset, font=("Manrope", 16, "bold"), padx=20, pady=10)
        self.reset_button.pack(side=tk.LEFT, padx=20, pady=20)
        # Back button 
        self.back_button = tk.Button(self, text="Trở về", command=self.back, font=("Manrope", 16, "bold"), padx=20, pady=10)
        self.back_button.pack(side=tk.RIGHT, padx=20, pady=20)

        # Status label
        self.status_label = tk.Label(self, text="", font=("Manrope", 20))
        self.status_label.pack(pady=10)

    # Hiển thị các đường kẻ trên bảng
    def show_lines(self):
        self.canvas.delete("all") # Xóa tất cả các phần tử trên canvas
        for col in range(1, self.size):
            x = col * self.sqsize
            self.canvas.create_line(x, 0, x, DEFAULT_HEIGHT, fill=LINE_COLOR, width=self.line_width)
        for row in range(1, self.size):
            y = row * self.sqsize
            self.canvas.create_line(0, y, DEFAULT_WIDTH, y, fill=LINE_COLOR, width=self.line_width)

    # Vẽ ký hiệu X hoặc O lên bàn cờ
    def draw_fig(self, row, col):
        if self.board.squares[row][col] == 1:
            start_desc = (col * self.sqsize + self.offset, row * self.sqsize + self.offset)
            end_desc = (col * self.sqsize + self.sqsize - self.offset, row * self.sqsize + self.sqsize - self.offset)
            self.canvas.create_line(*start_desc, *end_desc, fill=CROSS_COLOR, width=self.cross_width)

            start_asc = (col * self.sqsize + self.offset, row * self.sqsize + self.sqsize - self.offset)
            end_asc = (col * self.sqsize + self.sqsize - self.offset, row * self.sqsize + self.offset)
            self.canvas.create_line(*start_asc, *end_asc, fill=CROSS_COLOR, width=self.cross_width)
        elif self.board.squares[row][col] == 2:
            center = (col * self.sqsize + self.sqsize // 2, row * self.sqsize + self.sqsize // 2)
            self.canvas.create_oval(center[0] - self.radius, center[1] - self.radius,
                                    center[0] + self.radius, center[1] + self.radius,
                                    outline=CIRC_COLOR, width=self.circ_width)

    def make_move(self, row, col):
        if self.board.empty_sqr(row, col):
            self.board.mark_sqr(row, col, self.player)
            self.draw_fig(row, col)
            self.canvas.update()  # Cập nhật canvas ngay lập tức
            self.next_turn()
            return True
        return False

    def next_turn(self):
        self.player = self.player % 2 + 1 # Chuyển lượt người chơi
        self.status_label.config(text=f"Lượt của Người chơi {self.player}")  # Cập nhật status label
    
    # Hàm kẻ đường win 
    def draw_winning_line(self):
        if self.board.winning_line:
            start, end = self.board.winning_line
            start_x = start[1] * self.sqsize + self.sqsize // 2
            start_y = start[0] * self.sqsize + self.sqsize // 2
            end_x = end[1] * self.sqsize + self.sqsize // 2
            end_y = end[0] * self.sqsize + self.sqsize // 2
            # Tính toán độ dài của đường kẻ chiến thắng
            delta_x = end_x - start_x
            delta_y = end_y - start_y
            start_x -= delta_x * (WIN_LINE_LENGTH - 1) / 2
            start_y -= delta_y * (WIN_LINE_LENGTH - 1) / 2
            end_x += delta_x * (WIN_LINE_LENGTH - 1) / 2
            end_y += delta_y * (WIN_LINE_LENGTH - 1) / 2
            self.canvas.create_line(start_x, start_y, end_x, end_y, fill=WIN_LINE_COLOR, width=WIN_LINE_WIDTH)
            

    def is_over(self, row, col):
        result = self.board.final_state(row, col)
        if result != 0:
            winner = "Người chơi 1" if result == 1 else "Người chơi 2"
            self.draw_winning_line()
            messagebox.showinfo("Kết quả", f"{winner} đã thắng")  # Hiển thị hộp thoại thông báo
            self.running = False
            self.status_label.config(text=f"{winner} đã thắng") # Cập nhật status label
            return True
        elif self.board.is_full(): #Hòa
            messagebox.showinfo("Kết quả", "Hòa")
            self.running = False # Dừng trò chơi
            self.status_label.config(text="Hòa") #Cập nhật status label
            return True
        return False

    def handle_click(self, event):
        if not self.running or self.ai_thinking: # Nếu trò chơi không chạy hoặc AI đang suy nghĩ
            return

        col = event.x // self.sqsize # Tính toán cột
        row = event.y // self.sqsize # Tính toán hàng

        if self.board.empty_sqr(row, col): # Nếu ô vuông trống
            if self.gamemode == 'pvp' or self.player == 1:
                if self.make_move(row, col): # Thực hiện nước đi
                    self.canvas.update()  # Cập nhật canvas ngay lập tức
                    if not self.is_over(row, col): # Nếu trò chơi chưa kết thúc
                        if self.gamemode == 'ai' and self.running:
                            self.status_label.config(text="AI đang suy nghĩ...")
                            self.update()  # Cập nhật giao diện ngay lập tức
                            self.after(100, self.ai_turn) # AI thực hiện nước đi
        else:
            self.status_label.config(text="Ô này đã được đánh!") # Hiển thị thông báo ô đã được đánh
            self.update()  # Cập nhật giao diện ngay lập tức

    def ai_turn(self):
        self.ai_thinking = True
        self.status_label.config(text="AI đang suy nghĩ...")
        self.update()  # Cập nhật giao diện ngay lập tức
        
        def ai_move():
            move = self.ai.eval(self.board) # AI tính toán nước đi
            if move:
                self.after(0, lambda: self.make_ai_move(move))
            else:
                self.after(0, self.handle_ai_no_move)
        self.after(100, ai_move)  # Sử dụng after thay vì threading

    def make_ai_move(self, move):
        row, col = move
        if self.make_move(row, col):  # AI thực hiện nước đi
            self.canvas.update()  # Cập nhật canvas ngay lập tức
            if not self.is_over(row, col): # Nếu trò chơi chưa kết thúc
                self.status_label.config(text="Lượt của bạn")
            self.ai_thinking = False
        else:
            print("AI không thể thực hiện nước đi này!")
            self.handle_ai_no_move()

    def handle_ai_no_move(self):
        print("AI không tìm được nước đi hợp lệ!")
        empty_sqrs = self.board.get_empty_sqrs()
        if empty_sqrs:
            move = random.choice(empty_sqrs) # Chọn ngẫu nhiên nước đi
            self.make_ai_move(move)
        else:
            self.status_label.config(text="Hòa - Không còn nước đi!") # Hiển thị thông báo hòa
            self.running = False
        self.ai_thinking = False

    def reset(self):
        self.board = Board(self.size)  # Khởi tạo lại bàn cờ
        self.running = True  # Bắt đầu trò chơi mới
        self.ai_thinking = False
        self.player = 1  # Đặt lại người chơi về người chơi 1
        self.show_lines()  # Vẽ lại lưới
        self.status_label.config(text="Bắt đầu trò chơi mới. Lượt của Người chơi 1")  # Cập nhật status label
        self.canvas.delete("all")  # Xóa tất cả các phần tử trên canvas
        self.show_lines()  # Vẽ lại lưới
        self.board.winning_line = None  # Đặt lại đường thắng
    
        # Nếu đang ở chế độ AI và AI đi trước (người chơi 2), thực hiện nước đi của AI
        if self.gamemode == 'ai' and self.player == 2:
            self.after(100, self.ai_turn)
    
        self.update()  # Cập nhật giao diện

    def back(self):
        self.destroy() # Đóng cửa sổ hiện tại
        import caro_menu # Quay lại form menu
        root = tk.Tk() # Tạo cửa sổ mới
        caro_menu.CaroUI(root) # Khởi tạo giao diện menu
        root.mainloop() # Chạy vòng lặp chính của giao diện

    def update(self):
        self.canvas.update() # Cập nhật canvas
        self.update_idletasks() # Cập nhật các tác vụ nền

if __name__ == '__main__':
    game = Game() # Tạo đối tượng game
    game.mainloop() # Bắt đầu vòng lặp chính của giao diện
