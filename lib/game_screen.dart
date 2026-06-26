import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'word_validator.dart';
import 'result_screen.dart';

class GameScreen extends StatefulWidget {
  const GameScreen({super.key});

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> with TickerProviderStateMixin {
  static const int _totalSeconds = 300;
  static const int _turnSeconds = 20;

  int _totalTime = _totalSeconds;
  int _turnTime = _turnSeconds;
  int _currentPlayer = 1;
  final Map<int, int> _scores = {1: 0, 2: 0};
  final Set<String> _usedWords = {};
  String _lastWord = '';
  late String _requiredLetter;
  String _statusText = 'Game started!';
  Color _statusColor = Colors.white70;
  bool _isValidating = false;

  Timer? _timer;
  final TextEditingController _inputController = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  late AnimationController _letterPulse;
  late AnimationController _statusShake;
  late Animation<double> _shakeAnim;

  @override
  void initState() {
    super.initState();
    _requiredLetter = String.fromCharCode('a'.codeUnitAt(0) + Random().nextInt(26));

    _letterPulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);

    _statusShake = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _shakeAnim = Tween<double>(begin: 0, end: 8).animate(
      CurvedAnimation(parent: _statusShake, curve: Curves.elasticIn),
    );

    _startTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _inputController.dispose();
    _focusNode.dispose();
    _letterPulse.dispose();
    _statusShake.dispose();
    super.dispose();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        _totalTime--;
        _turnTime--;
      });
      if (_totalTime <= 0 || _turnTime <= 0) {
        _timer?.cancel();
        _navigateToResult(timedOut: true);
      }
    });
  }

  Future<void> _submitWord() async {
    if (_isValidating) return;
    final word = _inputController.text.trim().toLowerCase();
    _inputController.clear();
    _focusNode.requestFocus();

    if (word.isEmpty || !RegExp(r'^[a-z]+$').hasMatch(word)) return;

    if (_usedWords.contains(word)) {
      _showError('Already used!');
      return;
    }

    if (word[0] != _requiredLetter) {
      _showError('Must start with "${_requiredLetter.toUpperCase()}"');
      return;
    }

    setState(() => _isValidating = true);
    final valid = await WordValidator.isValidWord(word);
    if (!mounted) return;
    setState(() => _isValidating = false);

    if (!valid) {
      _showError('Not a valid English word!');
      return;
    }

    // Success
    HapticFeedback.lightImpact();
    final score = WordValidator.calculateScore(word);
    setState(() {
      _scores[_currentPlayer] = _scores[_currentPlayer]! + score;
      _usedWords.add(word);
      _lastWord = word;
      _requiredLetter = word[word.length - 1];
      _statusText = '+$score points!';
      _statusColor = const Color(0xFF00C853);
      _currentPlayer = _currentPlayer == 1 ? 2 : 1;
      _turnTime = _turnSeconds;
    });
    _letterPulse.reset();
    _letterPulse.repeat(reverse: true);
  }

  void _showError(String msg) {
    HapticFeedback.mediumImpact();
    setState(() {
      _statusText = msg;
      _statusColor = const Color(0xFFFF5252);
    });
    _statusShake.forward(from: 0);
  }

  void _navigateToResult({bool timedOut = false}) {
    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => ResultScreen(
          scores: _scores,
          usedWords: _usedWords,
          timedOut: timedOut,
        ),
      ),
    );
  }

  Color get _timerColor {
    if (_turnTime > 10) return const Color(0xFF00C853);
    if (_turnTime > 5) return const Color(0xFFFFD600);
    return const Color(0xFFFF5252);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildTopBar(),
              const SizedBox(height: 16),
              _buildPlayerCards(),
              const SizedBox(height: 20),
              _buildLetterDisplay(),
              const SizedBox(height: 20),
              _buildLastWord(),
              const Spacer(),
              _buildStatusText(),
              const SizedBox(height: 12),
              _buildInput(),
              const SizedBox(height: 12),
              _buildSubmitButton(),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    final totalMin = _totalTime ~/ 60;
    final totalSec = _totalTime % 60;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          '${totalMin.toString().padLeft(2, '0')}:${totalSec.toString().padLeft(2, '0')}',
          style: GoogleFonts.rubik(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: Colors.white54,
          ),
        ),
        Text(
          '${_usedWords.length} words',
          style: const TextStyle(color: Colors.white38, fontSize: 14),
        ),
        TextButton(
          onPressed: () => showDialog(
            context: context,
            builder: (_) => AlertDialog(
              backgroundColor: const Color(0xFF1A1A1A),
              title: const Text('Quit Game?'),
              actions: [
                TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                FilledButton(
                  onPressed: () {
                    _timer?.cancel();
                    Navigator.pop(context);
                    Navigator.pop(context);
                  },
                  style: FilledButton.styleFrom(backgroundColor: Colors.red),
                  child: const Text('Quit'),
                ),
              ],
            ),
          ),
          child: const Text('QUIT', style: TextStyle(color: Colors.white38)),
        ),
      ],
    );
  }

  Widget _buildPlayerCards() {
    return Row(
      children: [
        Expanded(child: _PlayerCard(
          label: 'PLAYER 1',
          score: _scores[1]!,
          isActive: _currentPlayer == 1,
          color: const Color(0xFF00C853),
        )),
        const SizedBox(width: 12),
        Expanded(child: _PlayerCard(
          label: 'PLAYER 2',
          score: _scores[2]!,
          isActive: _currentPlayer == 2,
          color: const Color(0xFF00E5FF),
        )),
      ],
    );
  }

  Widget _buildLetterDisplay() {
    return Column(
      children: [
        Text(
          'PLAYER $_currentPlayer — starts with',
          style: const TextStyle(color: Colors.white54, fontSize: 13, letterSpacing: 1.5),
        ),
        const SizedBox(height: 8),
        AnimatedBuilder(
          animation: _letterPulse,
          builder: (_, __) => Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFF1A1A1A),
              border: Border.all(
                color: Color.lerp(
                  const Color(0xFF00C853),
                  const Color(0xFF00E5FF),
                  _letterPulse.value,
                )!,
                width: 3,
              ),
              boxShadow: [
                BoxShadow(
                  color: Color.lerp(
                    const Color(0xFF00C853),
                    const Color(0xFF00E5FF),
                    _letterPulse.value,
                  )!.withOpacity(0.4),
                  blurRadius: 20,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Center(
              child: Text(
                _requiredLetter.toUpperCase(),
                style: GoogleFonts.rubik(
                  fontSize: 72,
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        // Turn timer arc
        _TurnTimerBar(seconds: _turnTime, maxSeconds: _turnSeconds, color: _timerColor),
        const SizedBox(height: 4),
        Text(
          '${_turnTime}s',
          style: TextStyle(
            color: _timerColor,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }

  Widget _buildLastWord() {
    if (_lastWord.isEmpty) return const SizedBox.shrink();
    return Center(
      child: Text(
        'Last: $_lastWord',
        style: const TextStyle(color: Colors.white38, fontSize: 14),
      ),
    );
  }

  Widget _buildStatusText() {
    return AnimatedBuilder(
      animation: _shakeAnim,
      builder: (_, child) => Transform.translate(
        offset: Offset(_statusShake.isAnimating ? sin(_shakeAnim.value * pi) * 6 : 0, 0),
        child: child,
      ),
      child: Text(
        _statusText,
        textAlign: TextAlign.center,
        style: TextStyle(
          color: _statusColor,
          fontSize: 15,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _buildInput() {
    return TextField(
      controller: _inputController,
      focusNode: _focusNode,
      autofocus: true,
      textCapitalization: TextCapitalization.none,
      style: GoogleFonts.rubik(fontSize: 28, fontWeight: FontWeight.w600),
      textAlign: TextAlign.center,
      inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[a-zA-Z]'))],
      decoration: InputDecoration(
        hintText: 'Type a word…',
        hintStyle: const TextStyle(color: Colors.white24),
        filled: true,
        fillColor: const Color(0xFF1A1A1A),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFF00C853), width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(vertical: 18, horizontal: 20),
      ),
      onSubmitted: (_) => _submitWord(),
    );
  }

  Widget _buildSubmitButton() {
    return FilledButton(
      onPressed: _isValidating ? null : _submitWord,
      style: FilledButton.styleFrom(
        backgroundColor: const Color(0xFF00C853),
        foregroundColor: Colors.black,
        padding: const EdgeInsets.symmetric(vertical: 18),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        textStyle: GoogleFonts.rubik(fontSize: 18, fontWeight: FontWeight.w700),
      ),
      child: _isValidating
          ? const SizedBox(
              height: 22,
              width: 22,
              child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2.5),
            )
          : const Text('SUBMIT'),
    );
  }
}

class _PlayerCard extends StatelessWidget {
  final String label;
  final int score;
  final bool isActive;
  final Color color;

  const _PlayerCard({
    required this.label,
    required this.score,
    required this.isActive,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        color: isActive ? color.withOpacity(0.15) : const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isActive ? color : Colors.white12,
          width: isActive ? 2 : 1,
        ),
      ),
      child: Column(
        children: [
          Text(label,
              style: TextStyle(
                color: isActive ? color : Colors.white38,
                fontSize: 11,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.5,
              )),
          const SizedBox(height: 4),
          Text(
            score.toString(),
            style: GoogleFonts.rubik(
              fontSize: 32,
              fontWeight: FontWeight.w900,
              color: isActive ? Colors.white : Colors.white54,
            ),
          ),
          if (isActive)
            Container(
              margin: const EdgeInsets.only(top: 4),
              width: 6,
              height: 6,
              decoration: BoxDecoration(color: color, shape: BoxShape.circle),
            ),
        ],
      ),
    );
  }
}

class _TurnTimerBar extends StatelessWidget {
  final int seconds;
  final int maxSeconds;
  final Color color;

  const _TurnTimerBar({required this.seconds, required this.maxSeconds, required this.color});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final fraction = (seconds / maxSeconds).clamp(0.0, 1.0);
      return Container(
        height: 6,
        width: constraints.maxWidth * 0.6,
        decoration: BoxDecoration(
          color: Colors.white12,
          borderRadius: BorderRadius.circular(3),
        ),
        child: FractionallySizedBox(
          alignment: Alignment.centerLeft,
          widthFactor: fraction,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 500),
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(3),
            ),
          ),
        ),
      );
    });
  }
}
