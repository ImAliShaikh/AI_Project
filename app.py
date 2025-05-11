from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

class NumberGuessingGame:
    def __init__(self):
        self.reset_game()
    
    def reset_game(self, difficulty='medium'):
        self.difficulty = difficulty
        self.target_number = ''.join(random.sample('0123456789', 4))
        print(f"Target number: {self.target_number}")  # For testing
        self.player_turn = True
        self.game_over = False
        self.winner = None
        self.player_guesses = []
        self.ai_guesses = []
        self.good_digits = set()  # digits that were correct in previous guesses
        self.bad_digits = set()   # digits that were incorrect
        self.current_positions = {}  # known correct positions for digits
        self.wrong_positions = {}  # known wrong positions for digits {pos: [digits]}
        
    def check_guess(self, guess):
        correct_digits = sum(1 for d in guess if d in self.target_number)
        correct_positions = sum(1 for i, d in enumerate(guess) if d == self.target_number[i])
        return correct_digits, correct_positions
    
    def update_knowledge(self, guess, correct_digits, correct_positions):
        # For easy mode, there's a chance we don't update knowledge
        if self.difficulty == 'easy' and random.random() < 0.4:
            return
            
        # For medium mode, there's a smaller chance we don't update knowledge
        if self.difficulty == 'medium' and random.random() < 0.15:
            return
        
        # Update good and bad digits
        if correct_digits == 0:
            # All digits in this guess are wrong
            self.bad_digits.update(set(guess))
        else:
            # Some digits are correct
            for digit in guess:
                if digit in self.target_number:
                    self.good_digits.add(digit)
                else:
                    self.bad_digits.add(digit)
        
        # Update position information
        for i, digit in enumerate(guess):
            if digit == self.target_number[i]:
                self.current_positions[i] = digit
            else:
                if i not in self.wrong_positions:
                    self.wrong_positions[i] = []
                if digit not in self.wrong_positions[i]:
                    self.wrong_positions[i].append(digit)
    
    def ai_guess(self):
        # Different strategies based on difficulty
        if self.difficulty == 'easy':
            return self.easy_ai_guess()
        elif self.difficulty == 'medium':
            return self.medium_ai_guess()
        else:  # hard
            return self.hard_ai_guess()
    
    def easy_ai_guess(self):
        # For easy mode, AI has limited memory and makes more mistakes
        
        # 30% chance of a completely random guess regardless of knowledge
        if random.random() < 0.30:
            guess = ''.join(random.sample('0123456789', 4))
            self.ai_guesses.append(guess)
            correct_digits, correct_positions = self.check_guess(guess)
            self.update_knowledge(guess, correct_digits, correct_positions)
            return guess, correct_digits, correct_positions
        
        # For easy mode, AI only remembers the last 2 guesses
        memory_limit = 2
        limited_ai_guesses = self.ai_guesses[-memory_limit:] if len(self.ai_guesses) > memory_limit else self.ai_guesses
        
        # Limited memory of good and bad digits
        temp_good_digits = set()
        temp_bad_digits = set()
        temp_positions = {}
        
        # Build knowledge only from recent guesses
        for guess in limited_ai_guesses:
            digits, positions = self.check_guess(guess)
            if digits == 0:
                temp_bad_digits.update(set(guess))
            else:
                for i, d in enumerate(guess):
                    if d == self.target_number[i]:
                        temp_positions[i] = d
                        temp_good_digits.add(d)
        
        # Create new guess with limited knowledge
        guess_list = [''] * 4
        
        # Place known correct positions (with 40% chance of ignoring each)
        for pos, digit in temp_positions.items():
            if random.random() > 0.4:  # 60% chance of using correct knowledge
                guess_list[pos] = digit
        
        # Fill remaining positions
        remaining_positions = [i for i in range(4) if not guess_list[i]]
        
        # 50% chance of using previous knowledge for remaining positions
        if random.random() < 0.5 and temp_good_digits:
            available_digits = list(temp_good_digits - set([d for d in guess_list if d]))
            # Fill with known good digits first if available
            for pos in remaining_positions[:]:
                if available_digits:
                    digit = random.choice(available_digits)
                    guess_list[pos] = digit
                    available_digits.remove(digit)
                    remaining_positions.remove(pos)
        
        # Fill any remaining positions with random digits
        unused_digits = list(set('0123456789') - set([d for d in guess_list if d]))
        random.shuffle(unused_digits)
        
        for pos in remaining_positions:
            if unused_digits:
                guess_list[pos] = unused_digits.pop(0)
        
        # Make sure all positions are filled
        for i in range(4):
            if not guess_list[i]:
                guess_list[i] = random.choice('0123456789')
        
        # Check for duplicates and fix them
        for i in range(4):
            for j in range(i+1, 4):
                if guess_list[i] == guess_list[j]:
                    unused = list(set('0123456789') - set(guess_list))
                    if unused:
                        guess_list[j] = random.choice(unused)
        
        guess = ''.join(guess_list)
        self.ai_guesses.append(guess)
        correct_digits, correct_positions = self.check_guess(guess)
        self.update_knowledge(guess, correct_digits, correct_positions)
        return guess, correct_digits, correct_positions
    
    def medium_ai_guess(self):
        # First guess is always random
        if not self.ai_guesses:
            guess = ''.join(random.sample('0123456789', 4))
            self.ai_guesses.append(guess)
            correct_digits, correct_positions = self.check_guess(guess)
            self.update_knowledge(guess, correct_digits, correct_positions)
            return guess, correct_digits, correct_positions
        
        # 15% chance of making a partially random guess
        if random.random() < 0.15:
            # Use 50% knowledge-based and 50% random
            guess_list = [''] * 4
            
            # Use some correct positions
            for pos, digit in self.current_positions.items():
                if random.random() < 0.7:  # 70% chance of using correct knowledge
                    guess_list[pos] = digit
            
            # Fill remaining with random digits
            remaining_positions = [i for i in range(4) if not guess_list[i]]
            unused_digits = list(set('0123456789') - set([d for d in guess_list if d]))
            random.shuffle(unused_digits)
            
            for pos in remaining_positions:
                if unused_digits:
                    guess_list[pos] = unused_digits.pop(0)
            
            guess = ''.join(guess_list)
            self.ai_guesses.append(guess)
            correct_digits, correct_positions = self.check_guess(guess)
            self.update_knowledge(guess, correct_digits, correct_positions)
            return guess, correct_digits, correct_positions
        
        # Create informed guess using known information
        guess_list = [''] * 4
        
        # Place known correct positions with occasional mistakes
        for pos, digit in self.current_positions.items():
            if random.random() < 0.8:  # 80% chance of using correct position
                guess_list[pos] = digit
        
        # Fill remaining positions
        remaining_positions = [i for i in range(4) if not guess_list[i]]
        available_digits = list(self.good_digits - set([d for d in guess_list if d]))
        
        if not available_digits:
            # If we don't have any known good digits, use digits we haven't tried
            available_digits = list(set('0123456789') - self.bad_digits - set([d for d in guess_list if d]))
        
        # Shuffle available digits to try different combinations
        random.shuffle(available_digits)
        
        # Fill remaining positions avoiding known wrong positions with occasional mistakes
        for pos in remaining_positions:
            wrong_digits = self.wrong_positions.get(pos, [])
            if random.random() < 0.2:  # 20% chance of ignoring wrong position info
                valid_digits = available_digits
            else:
                valid_digits = [d for d in available_digits if d not in wrong_digits and d not in guess_list]
            
            if valid_digits:
                digit = valid_digits[0]
                guess_list[pos] = digit
                if digit in available_digits:
                    available_digits.remove(digit)
            elif available_digits:
                digit = available_digits[0]
                guess_list[pos] = digit
                available_digits.remove(digit)
            else:
                # If we run out of available digits, use any unused digit
                unused = list(set('0123456789') - set([d for d in guess_list if d]))
                if unused:
                    guess_list[pos] = random.choice(unused)
        
        # Check for empty spots and fill with random digits
        for i in range(4):
            if not guess_list[i]:
                unused = list(set('0123456789') - set([d for d in guess_list if d]))
                if unused:
                    guess_list[i] = random.choice(unused)
                else:
                    guess_list[i] = random.choice('0123456789')
        
        # Check for duplicates and fix them
        for i in range(4):
            for j in range(i+1, 4):
                if guess_list[i] == guess_list[j]:
                    unused = list(set('0123456789') - set(guess_list))
                    if unused:
                        guess_list[j] = random.choice(unused)
        
        guess = ''.join(guess_list)
        self.ai_guesses.append(guess)
        correct_digits, correct_positions = self.check_guess(guess)
        self.update_knowledge(guess, correct_digits, correct_positions)
        return guess, correct_digits, correct_positions
    
    def hard_ai_guess(self):
        # First guess is always random
        if not self.ai_guesses:
            guess = ''.join(random.sample('0123456789', 4))
            self.ai_guesses.append(guess)
            correct_digits, correct_positions = self.check_guess(guess)
            self.update_knowledge(guess, correct_digits, correct_positions)
            return guess, correct_digits, correct_positions
        
        # Only 5% chance of making a mistake in hard mode
        if random.random() < 0.05:
            # Swap two positions
            temp_guess = self.create_optimal_guess()
            guess_list = list(temp_guess)
            # Swap two random positions
            pos1, pos2 = random.sample(range(4), 2)
            guess_list[pos1], guess_list[pos2] = guess_list[pos2], guess_list[pos1]
            guess = ''.join(guess_list)
            self.ai_guesses.append(guess)
            correct_digits, correct_positions = self.check_guess(guess)
            self.update_knowledge(guess, correct_digits, correct_positions)
            return guess, correct_digits, correct_positions
        
        # Hard mode has advanced logic to create optimal guesses
        guess = self.create_optimal_guess()
        self.ai_guesses.append(guess)
        correct_digits, correct_positions = self.check_guess(guess)
        self.update_knowledge(guess, correct_digits, correct_positions)
        return guess, correct_digits, correct_positions
    
    def create_optimal_guess(self):
        guess_list = [''] * 4
        
        # Place known correct positions
        for pos, digit in self.current_positions.items():
            guess_list[pos] = digit
        
        # Calculate which digits we know must be in the solution
        confirmed_digits = set(self.current_positions.values())
        potential_digits = self.good_digits - confirmed_digits
        
        # Fill remaining positions strategically
        remaining_positions = [i for i in range(4) if not guess_list[i]]
        
        # Use advanced logic to deduce next best moves
        for pos in remaining_positions:
            # Skip positions we've already filled
            if guess_list[pos]:
                continue
                
            # Get digits we know are wrong in this position
            wrong_digits = self.wrong_positions.get(pos, [])
            
            # Prioritize using digits we know are in the solution but don't know where
            candidates = [d for d in potential_digits if d not in wrong_digits and d not in guess_list]
            
            if candidates:
                # Use a digit we know is in solution but don't know where
                guess_list[pos] = candidates[0]
                potential_digits.remove(candidates[0])
            else:
                # If no known good digits left, try unused digits
                unknown_digits = list(set('0123456789') - self.good_digits - self.bad_digits)
                valid_choices = [d for d in unknown_digits if d not in wrong_digits and d not in guess_list]
                
                if valid_choices:
                    guess_list[pos] = valid_choices[0]
                elif self.bad_digits:
                    # If we've exhausted all other options, use a bad digit as last resort
                    valid_bad = [d for d in list(self.bad_digits) if d not in wrong_digits and d not in guess_list]
                    if valid_bad:
                        guess_list[pos] = valid_bad[0]
                    else:
                        # Truly last resort - use any available digit
                        unused = list(set('0123456789') - set([d for d in guess_list if d]))
                        if unused:
                            guess_list[pos] = unused[0]
                        else:
                            # This should never happen, but just in case
                            guess_list[pos] = random.choice('0123456789')
        
        # Final check for empty slots
        for i in range(4):
            if not guess_list[i]:
                unused = list(set('0123456789') - set([d for d in guess_list if d]))
                if unused:
                    guess_list[i] = unused[0]
                else:
                    # This should never happen, but just in case
                    guess_list[i] = random.choice('0123456789')
        
        # Check for duplicates
        digit_counts = {}
        for digit in guess_list:
            if digit in digit_counts:
                digit_counts[digit] += 1
            else:
                digit_counts[digit] = 1
        
        # Fix any duplicates
        if any(count > 1 for count in digit_counts.values()):
            # Find duplicate digits
            duplicates = [digit for digit, count in digit_counts.items() if count > 1]
            
            # Find unused digits
            unused_digits = list(set('0123456789') - set(guess_list))
            
            # Replace duplicates (except the first occurrence)
            for digit in duplicates:
                positions = [i for i, d in enumerate(guess_list) if d == digit]
                # Keep the first occurrence, replace others
                for pos in positions[1:]:
                    if unused_digits:
                        replacement = unused_digits.pop(0)
                        guess_list[pos] = replacement
                    else:
                        # If no unused digits left, just make it different from others
                        replacement = next(d for d in '0123456789' if d not in guess_list)
                        guess_list[pos] = replacement
        
        return ''.join(guess_list)

game = NumberGuessingGame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset', methods=['POST'])
def reset():
    data = request.get_json()
    difficulty = data.get('difficulty', 'medium')
    game.reset_game(difficulty)
    return jsonify({'status': 'success'})

@app.route('/guess', methods=['POST'])
def make_guess():
    if game.game_over:
        return jsonify({'status': 'game_over', 'winner': game.winner})
    
    data = request.get_json()
    player_guess = data['guess']
    
    # Player's turn
    correct_digits, correct_positions = game.check_guess(player_guess)
    game.update_knowledge(player_guess, correct_digits, correct_positions)
    game.player_guesses.append(player_guess)
    
    if correct_positions == 4:
        game.game_over = True
        game.winner = 'player'
        return jsonify({
            'status': 'game_over',
            'winner': 'player',
            'player_guess': player_guess,
            'player_feedback': {  # Changed from 'feedback' to 'player_feedback' for consistency
                'correct_digits': correct_digits,
                'correct_positions': correct_positions
            }
        })
    
    # AI's turn
    ai_guess, ai_correct_digits, ai_correct_positions = game.ai_guess()
    
    if ai_correct_positions == 4:
        game.game_over = True
        game.winner = 'ai'
        return jsonify({
            'status': 'game_over',
            'winner': 'ai',
            'player_guess': player_guess,
            'player_feedback': {
                'correct_digits': correct_digits,
                'correct_positions': correct_positions
            },
            'ai_guess': ai_guess,
            'ai_feedback': {
                'correct_digits': ai_correct_digits,
                'correct_positions': ai_correct_positions
            }
        })
    
    return jsonify({
        'status': 'success',
        'player_guess': player_guess,
        'player_feedback': {
            'correct_digits': correct_digits,
            'correct_positions': correct_positions
        },
        'ai_guess': ai_guess,
        'ai_feedback': {
            'correct_digits': ai_correct_digits,
            'correct_positions': ai_correct_positions
        }
    })

if __name__ == '__main__':
    app.run(debug=True)