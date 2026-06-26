import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'main.dart';

class ResultScreen extends StatelessWidget {
  final Map<int, int> scores;
  final Set<String> usedWords;
  final bool timedOut;

  const ResultScreen({
    super.key,
    required this.scores,
    required this.usedWords,
    required this.timedOut,
  });

  @override
  Widget build(BuildContext context) {
    final p1 = scores[1]!;
    final p2 = scores[2]!;
    final String winner;
    final Color winnerColor;

    if (p1 > p2) {
      winner = 'PLAYER 1 WINS!';
      winnerColor = const Color(0xFF00C853);
    } else if (p2 > p1) {
      winner = 'PLAYER 2 WINS!';
      winnerColor = const Color(0xFF00E5FF);
    } else {
      winner = "IT'S A DRAW!";
      winnerColor = const Color(0xFFFFD600);
    }

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              Text(
                'FINAL SCORE',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white38, fontSize: 13, letterSpacing: 2),
              ),
              const SizedBox(height: 12),
              Text(
                winner,
                textAlign: TextAlign.center,
                style: GoogleFonts.rubik(
                  fontSize: 38,
                  fontWeight: FontWeight.w900,
                  color: winnerColor,
                ),
              ),
              const SizedBox(height: 8),
              if (timedOut)
                Text(
                  "Time's up!",
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white38, fontSize: 14),
                ),
              const SizedBox(height: 40),
              Row(
                children: [
                  Expanded(
                    child: _ScoreCard(
                      label: 'PLAYER 1',
                      score: p1,
                      color: const Color(0xFF00C853),
                      isWinner: p1 > p2,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _ScoreCard(
                      label: 'PLAYER 2',
                      score: p2,
                      color: const Color(0xFF00E5FF),
                      isWinner: p2 > p1,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1A1A),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _StatItem(value: '${usedWords.length}', label: 'Words Played'),
                    _StatItem(
                      value: '${p1 + p2}',
                      label: 'Total Points',
                    ),
                    _StatItem(
                      value: usedWords.isEmpty
                          ? '0'
                          : '${((p1 + p2) / usedWords.length).toStringAsFixed(1)}',
                      label: 'Avg/Word',
                    ),
                  ],
                ),
              ),
              if (usedWords.isNotEmpty) ...[
                const SizedBox(height: 20),
                const Text('Words Used',
                    style: TextStyle(color: Colors.white54, fontSize: 13, letterSpacing: 1)),
                const SizedBox(height: 8),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: SingleChildScrollView(
                      child: Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: usedWords
                            .map((w) => Chip(
                                  label: Text(w),
                                  backgroundColor: const Color(0xFF2A2A2A),
                                  labelStyle: const TextStyle(color: Colors.white70, fontSize: 12),
                                  padding: EdgeInsets.zero,
                                ))
                            .toList(),
                      ),
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 20),
              FilledButton(
                onPressed: () => Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(builder: (_) => const HomeScreen()),
                  (_) => false,
                ),
                style: FilledButton.styleFrom(
                  backgroundColor: const Color(0xFF00C853),
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  textStyle: GoogleFonts.rubik(fontSize: 18, fontWeight: FontWeight.w700),
                ),
                child: const Text('PLAY AGAIN'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ScoreCard extends StatelessWidget {
  final String label;
  final int score;
  final Color color;
  final bool isWinner;

  const _ScoreCard({
    required this.label,
    required this.score,
    required this.color,
    required this.isWinner,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isWinner ? color.withOpacity(0.15) : const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isWinner ? color : Colors.white12,
          width: isWinner ? 2 : 1,
        ),
      ),
      child: Column(
        children: [
          if (isWinner)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Icon(Icons.emoji_events_rounded, color: color, size: 22),
            ),
          Text(
            label,
            style: TextStyle(
              color: isWinner ? color : Colors.white38,
              fontSize: 12,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            score.toString(),
            style: GoogleFonts.rubik(
              fontSize: 52,
              fontWeight: FontWeight.w900,
              color: isWinner ? Colors.white : Colors.white54,
            ),
          ),
          Text(
            'pts',
            style: TextStyle(color: isWinner ? color : Colors.white38, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String value;
  final String label;

  const _StatItem({required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: GoogleFonts.rubik(
                fontSize: 28, fontWeight: FontWeight.w800, color: Colors.white)),
        Text(label, style: const TextStyle(color: Colors.white38, fontSize: 11)),
      ],
    );
  }
}
