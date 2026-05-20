import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final HttpService _httpService = HttpService();
  
  bool _isLoading = false;
  bool _obscureText = true;
  bool _showResend = false;

  void _login() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      _showError("Email and Password are required.");
      return;
    }

    setState(() {
      _isLoading = true;
      _showResend = false;
    });

    try {
      final AuthResponse res = await Supabase.instance.client.auth.signInWithPassword(
        email: email, 
        password: password
      );
      if (res.session != null) {
        Navigator.pushReplacementNamed(context, '/chat');
      }
    } on AuthException catch (e) {
      _showError(e.message);
      if (e.message.toLowerCase().contains("email not confirmed") || e.message.toLowerCase().contains("verify")) {
        setState(() => _showResend = true);
      }
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _resendConfirmation() async {
    setState(() => _isLoading = true);
    try {
      await _httpService.resendConfirmation(_emailController.text.trim());
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Confirmation email resent. Check your inbox."), backgroundColor: Colors.green),
      );
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F2F5),
      body: Center(
        child: SingleChildScrollView(
          child: Container(
            constraints: BoxConstraints(maxWidth: 400),
            padding: EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.handyman, size: 64, color: const Color(0xFF075E54)),
                SizedBox(height: 16),
                Text("Service Orchestrator", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: const Color(0xFF075E54))),
                SizedBox(height: 8),
                Text("Login to your account", style: TextStyle(color: Colors.grey[700])),
                SizedBox(height: 32),
                TextField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(
                    hintText: "Email",
                    prefixIcon: Icon(Icons.email, color: const Color(0xFF075E54)),
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                  ),
                ),
                SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: _obscureText,
                  decoration: InputDecoration(
                    hintText: "Password",
                    prefixIcon: Icon(Icons.lock, color: const Color(0xFF075E54)),
                    suffixIcon: IconButton(
                      icon: Icon(_obscureText ? Icons.visibility : Icons.visibility_off, color: Colors.grey),
                      onPressed: () => setState(() => _obscureText = !_obscureText),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                  ),
                ),
                SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _login,
                    child: _isLoading ? SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : Text("Login"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF075E54),
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                if (_showResend) ...[
                  SizedBox(height: 8),
                  TextButton(
                    onPressed: _isLoading ? null : _resendConfirmation,
                    child: Text("Resend confirmation email", style: TextStyle(color: Colors.orange)),
                  )
                ],
                SizedBox(height: 16),
                TextButton(
                  onPressed: () => Navigator.pushReplacementNamed(context, '/register'),
                  child: Text("Don't have an account? Register", style: TextStyle(color: const Color(0xFF128C7E))),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }
}
