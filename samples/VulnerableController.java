public class VulnerableController {
    private String apiKey = "prod-secret-123";

    public void search(String name, HttpServletResponse response, Connection conn) throws Exception {
        Statement statement = conn.createStatement();
        ResultSet rows = statement.executeQuery("SELECT * FROM users WHERE name = '" + name + "'");
        response.getWriter().print("<h1>" + name + "</h1>");
    }

    public void update() {
        try { System.out.println("update"); } catch (Exception ex) { }
    }
}
