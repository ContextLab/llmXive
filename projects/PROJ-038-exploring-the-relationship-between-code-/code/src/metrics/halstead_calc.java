import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

/**
 * Halstead Complexity Metrics Calculator for Java Files.
 *
 * This program reads a Java source file, tokenizes it to identify
 * operators and operands, and calculates Halstead metrics.
 *
 * Usage: java HalsteadCalc <filename>
 * Output: Prints metrics in a parseable format:
 *         HALSTEAD: volume=<double>, n1=<int>, n2=<int>, N1=<int>, N2=<int>
 *
 * If the file cannot be parsed (syntax error), it prints:
 *         HALSTEAD: ERROR=<message>
 */
public class halstead_calc {

    // Operators in Java
    private static final Set<String> OPERATORS = new HashSet<>(Arrays.asList(
        // Arithmetic
        "+", "-", "*", "/", "%",
        // Relational
        "==", "!=", "<", ">", "<=", ">=",
        // Logical
        "&&", "||", "!",
        // Bitwise
        "&", "|", "^", "~", "<<", ">>", ">>>",
        // Assignment
        "=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>=", ">>>=",
        // Increment/Decrement
        "++", "--",
        // Ternary
        "?", ":",
        // Scope/Access
        ".", "::",
        // Cast
        "(", // treated as operator for grouping context
        ")",
        // Array access
        "[", "]",
        // Lambda
        "->",
        // instanceof
        "instanceof"
    ));

    // Keywords that act as operands (identifiers that are not operators)
    private static final Set<String> KEYWORDS = new HashSet<>(Arrays.asList(
        "abstract", "assert", "boolean", "break", "byte", "case", "catch",
        "char", "class", "const", "continue", "default", "do", "double",
        "else", "enum", "extends", "final", "finally", "float", "for",
        "goto", "if", "implements", "import", "instanceof", "int", "interface",
        "long", "native", "new", "package", "private", "protected", "public",
        "return", "short", "static", "strictfp", "super", "switch", "synchronized",
        "this", "throw", "throws", "transient", "try", "void", "volatile", "while"
    ));

    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java halstead_calc <filename>");
            System.exit(1);
        }

        String filename = args[0];
        try {
            String content = new String(Files.readAllBytes(Paths.get(filename)));
            Map<String, Double> metrics = calculateHalstead(content);
            System.out.printf("HALSTEAD: volume=%.4f, n1=%d, n2=%d, N1=%d, N2=%d%n",
                    metrics.get("volume"),
                    (int)metrics.get("n1"),
                    (int)metrics.get("n2"),
                    (int)metrics.get("N1"),
                    (int)metrics.get("N2"));
        } catch (IOException e) {
            System.out.println("HALSTEAD: ERROR=IO_ERROR: " + e.getMessage());
        } catch (Exception e) {
            System.out.println("HALSTEAD: ERROR=PARSE_ERROR: " + e.getMessage());
        }
    }

    public static Map<String, Double> calculateHalstead(String code) {
        Map<String, Double> result = new HashMap<>();
        
        // Tokenize
        List<String> tokens = tokenize(code);
        
        // Separate operators and operands
        Map<String, Integer> uniqueOperators = new HashMap<>();
        Map<String, Integer> uniqueOperands = new HashMap<>();
        int totalOperators = 0;
        int totalOperands = 0;

        for (String token : tokens) {
            if (isOperator(token)) {
                uniqueOperators.put(token, uniqueOperators.getOrDefault(token, 0) + 1);
                totalOperators++;
            } else if (isOperand(token)) {
                uniqueOperands.put(token, uniqueOperands.getOrDefault(token, 0) + 1);
                totalOperands++;
            }
        }

        int n1 = uniqueOperators.size(); // Number of unique operators
        int n2 = uniqueOperands.size();  // Number of unique operands
        int N1 = totalOperators;         // Total number of operators
        int N2 = totalOperands;          // Total number of operands

        double n = n1 + n2;
        double N = N1 + N2;
        double volume = 0.0;

        if (n > 0 && N > 0) {
            volume = N * Math.log2(n);
        }

        result.put("n1", (double)n1);
        result.put("n2", (double)n2);
        result.put("N1", (double)N1);
        result.put("N2", (double)N2);
        result.put("volume", volume);

        return result;
    }

    private static List<String> tokenize(String code) {
        List<String> tokens = new ArrayList<>();
        // Regex to match operators, identifiers, literals, and punctuation
        // This is a simplified tokenizer. For robust parsing, a full parser is needed.
        // We handle multi-character operators first by order of checking.
        
        String regex = "(?s)(//.*|/\\*[\\s\\S]*?\\*/|\"(?:[^\"\\\\]|\\\\.)*\"|'(?:[^'\\\\]|\\\\.)*'|\\d+\\.?\\d*|[a-zA-Z_][a-zA-Z0-9_]*|\\{\\}|[{}()\\[\\];,]|\\+\\+|--|\\+=|-=|\\*=|/=|%=|&=|\\|=|\\^=|<<=|>>=|>>>=|==|!=|<=|>=|&&|\\|\\||->|::|\\?|:|\\.|\\(|\\)|\\[|\\]|\\+|-|\\*|/|%|<|>|!|&|\\||\\^|~|<<|>>|>>>|=|;|,|\\{|\\})";
        
        Pattern pattern = Pattern.compile(regex);
        Matcher matcher = pattern.matcher(code);
        
        while (matcher.find()) {
            String token = matcher.group();
            if (token != null && !token.trim().isEmpty() && !token.startsWith("//") && !token.startsWith("/*")) {
                tokens.add(token);
            }
        }
        
        return tokens;
    }

    private static boolean isOperator(String token) {
        return OPERATORS.contains(token);
    }

    private static boolean isOperand(String token) {
        // Literals (numbers, strings, chars) are operands
        if (token.matches("\".*\"") || token.matches("\'.*\'") || token.matches("\\d+\\.?\\d*")) {
            return true;
        }
        // Identifiers that are not keywords are operands (variables, types, etc.)
        if (token.matches("[a-zA-Z_][a-zA-Z0-9_]*") && !KEYWORDS.contains(token)) {
            return true;
        }
        return false;
    }
}
