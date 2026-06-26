import 'dart:convert';
import 'package:http/http.dart' as http;

class WordValidator {
  static final Map<String, bool> _cache = {};

  static const Map<String, int> letterScores = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2, 'e': 1, 'f': 4, 'g': 2, 'h': 4,
    'i': 1, 'j': 8, 'k': 5, 'l': 1, 'm': 3, 'n': 1, 'o': 1, 'p': 3,
    'q': 10, 'r': 1, 's': 1, 't': 1, 'u': 1, 'v': 4, 'w': 4, 'x': 8,
    'y': 4, 'z': 10,
  };

  static int calculateScore(String word) {
    return word.toLowerCase().split('').fold(0, (sum, ch) => sum + (letterScores[ch] ?? 0));
  }

  static Future<bool> isValidWord(String word) async {
    final key = word.toLowerCase();
    if (_cache.containsKey(key)) return _cache[key]!;

    try {
      final uri = Uri.parse('https://api.dictionaryapi.dev/api/v2/entries/en/$key');
      final response = await http.get(uri).timeout(const Duration(seconds: 5));
      final valid = response.statusCode == 200;
      _cache[key] = valid;
      return valid;
    } catch (_) {
      // On network error, fall back to accepting the word to avoid blocking gameplay
      return true;
    }
  }
}
