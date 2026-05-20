import 'package:flutter/material.dart';
import '../services/api_service.dart';

class RegisterScreen extends StatefulWidget {
  @override
  _RegisterScreenState createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final TextEditingController _fullNameController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final HttpService _httpService = HttpService();
  
  bool _isLoading = false;
  bool _obscureText = true;

  String get _passwordStrength {
    final p = _passwordController.text;
    if (p.length < 6) return "Weak";
    if (p.length > 8 && p.contains(RegExp(r'[A-Z]')) && p.contains(RegExp(r'[0-9]'))) return "Strong";
    return "Medium";
  }

  void _register() async {
    final fullName = _fullNameController.text.trim();
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    final phone = _phoneController.text.trim();

    if (fullName.isEmpty || email.isEmpty || password.isEmpty || phone.isEmpty) {
      _showError("All fields are required.");
      return;
    }

    final RegExp emailRegex = RegExp(r"^[a-zA-Z0-9.a-zA-Z0-9.!#$%&'*+-/=?^_`{|}~]+@[a-zA-Z0-9]+\.[a-zA-Z]+");
    if (!emailRegex.hasMatch(email)) {
      _showError("Please enter a valid email address.");
      return;
    }

    if (password.length < 6) {
      _showError("Password must be at least 6 characters long.");
      return;
    }

    final RegExp phoneRegex = RegExp(r'^03[0-9]{9}$');
    if (!phoneRegex.hasMatch(phone)) {
      _showError("Please enter a valid 11-digit number starting with 03.");
      return;
    }

    setState(() => _isLoading = true);

    try {
      await _httpService.register(email, password, fullName, phone);
      _showSuccessDialog();
    } catch (e) {
      _showError(e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: Text("Registration Successful"),
        content: Text("Check your email. Click the link to verify your account."),
        actions: [
          TextButton(
            child: Text("I verified, go to Login", style: TextStyle(color: const Color(0xFF075E54))),
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.pushReplacementNamed(context, '/login');
            },
          )
        ],
      )
    );
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
                Text("Create Account", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: const Color(0xFF075E54))),
                SizedBox(height: 32),
                _buildTextField(_fullNameController, "Full Name", Icons.person, TextInputType.name),
                SizedBox(height: 16),
                _buildTextField(_emailController, "Email", Icons.email, TextInputType.emailAddress),
                SizedBox(height: 16),
                _buildPasswordField(),
                SizedBox(height: 16),
                _buildTextField(_phoneController, "Phone (03XXXXXXXXX)", Icons.phone, TextInputType.phone),
                SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _register,
                    child: _isLoading ? SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : Text("Register"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF075E54),
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                SizedBox(height: 16),
                TextButton(
                  onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
                  child: Text("Already have an account? Login", style: TextStyle(color: const Color(0xFF128C7E))),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(TextEditingController controller, String hint, IconData icon, TextInputType type) {
    return TextField(
      controller: controller,
      keyboardType: type,
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: Icon(icon, color: const Color(0xFF075E54)),
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      ),
    );
  }

  Widget _buildPasswordField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _passwordController,
          obscureText: _obscureText,
          onChanged: (v) => setState(() {}),
          decoration: InputDecoration(
            hintText: "Password (Min 6 chars)",
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
        if (_passwordController.text.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8, left: 12),
            child: Text("Strength: $_passwordStrength", style: TextStyle(
              color: _passwordStrength == 'Weak' ? Colors.red : 
                     _passwordStrength == 'Strong' ? Colors.green : Colors.orange,
              fontSize: 12
            )),
          )
      ],
    );
  }
}
