import java.io.*;
import java.util.*;
import java.nio.file.*;
import java.util.regex.*;

public class HalsteadCalc {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java -jar halstead_calc.jar <java_file>");
            System.exit(1);
        }

        String filePath = args[0];
        try {
            Map<String, Double> metrics = calculateHalstead(filePath);
            System.out.println("operators: " + metrics.get("operators"));
            System.out.println("operands: " + metrics.get("operands"));
            System.out.println("volume: " + metrics.get("volume"));
            System.out.println("length: " + metrics.get("length"));
            System.out.println("difficulty: " + metrics.get("difficulty"));
            System.out.println("effort: " + metrics.get("effort"));
            System.out.println("bugs: " + metrics.get("bugs"));
        } catch (Exception e) {
            System.err.println("Error processing file: " + e.getMessage());
            System.exit(1);
        }
    }

    public static Map<String, Double> calculateHalstead(String filePath) throws IOException {
        String content = new String(Files.readAllBytes(Paths.get(filePath)));
        
        // Simple tokenizer for Java (excluding comments and strings)
        // This is a basic implementation; a full parser would be more robust
        content = removeComments(content);
        content = removeStrings(content);
        
        List<String> tokens = tokenize(content);
        
        Map<String, Integer> operatorCounts = new HashMap<>();
        Map<String, Integer> operandCounts = new HashMap<>();
        
        // Define operators (simplified set)
        Set<String> operators = new HashSet<>(Arrays.asList(
            "+", "-", "*", "/", "%", "<", ">", "<=", ">=", "==", "!=", 
            "&&", "||", "!", "=", "+=", "-=", "*=", "/=", "%=", 
            "++", "--", "&", "|", "^", "~", "<<", ">>", ">>>",
            "?", ":", ".", "(", ")", "{", "}", "[", "]", ";", ","
        ));
        
        for (String token : tokens) {
            if (operators.contains(token)) {
                operatorCounts.put(token, operatorCounts.getOrDefault(token, 0) + 1);
            } else if (!token.isEmpty()) {
                // Assume everything else is an operand
                operandCounts.put(token, operandCounts.getOrDefault(token, 0) + 1);
            }
        }
        
        int n1 = operatorCounts.size(); // Number of unique operators
        int n2 = operandCounts.size();  // Number of unique operands
        
        int N1 = 0; // Total operators
        for (int count : operatorCounts.values()) N1 += count;
        
        int N2 = 0; // Total operands
        for (int count : operandCounts.values()) N2 += count;
        
        int N = N1 + N2; // Program length
        
        double volume = 0;
        if (N > 0) {
            volume = N * Math.log2(n1 + n2);
        }
        
        int estimatedLength = n1 * Math.log2(n1) + n2 * Math.log2(n2);
        double difficulty = 0;
        if (n2 > 0) {
            difficulty = (double) n1 / 2 * (double) N2 / n2;
        }
        
        double effort = difficulty * volume;
        double bugs = Math.pow(volume, 1.0/3.0) / 30.0;
        
        Map<String, Double> result = new HashMap<>();
        result.put("operators", (double) N1);
        result.put("operands", (double) N2);
        result.put("volume", volume);
        result.put("length", (double) N);
        result.put("difficulty", difficulty);
        result.put("effort", effort);
        result.put("bugs", bugs);
        
        return result;
    }

    private static String removeComments(String code) {
        // Remove single-line comments
        code = code.replaceAll("//.*", "");
        // Remove multi-line comments
        code = code.replaceAll("/\\*[^*]*\\*+(?:[^/*][^*]*\\*+)*/", "");
        return code;
    }

    private static String removeStrings(String code) {
        // Remove string literals
        code = code.replaceAll("\"[^\"\\\\]*(\\\\.[^\"\\\\]*)*\"", "\"\"");
        // Remove char literals
        code = code.replaceAll("'[^'\\\\]*(\\\\.[^'\\\\]*)*'", "''");
        return code;
    }

    private static List<String> tokenize(String code) {
        List<String> tokens = new ArrayList<>();
        // Simple regex tokenizer
        // Matches operators, identifiers, numbers, and symbols
        Pattern pattern = Pattern.compile(
            "[+\\-*/%<>=!&|^~?:;.,()\\[\\]{}]+" +
            "|[a-zA-Z_][a-zA-Z0-9_]*" +
            "|[0-9]+(\\.[0-9]+)?"
        );
        Matcher matcher = pattern.matcher(code);
        while (matcher.find()) {
            tokens.add(matcher.group());
        }
        return tokens;
    }
}
