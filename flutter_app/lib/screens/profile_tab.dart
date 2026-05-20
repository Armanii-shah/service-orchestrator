import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../services/api_service.dart';

class ProfileTab extends StatefulWidget {
  @override
  _ProfileTabState createState() => _ProfileTabState();
}

class _ProfileTabState extends State<ProfileTab> {
  final HttpService _httpService = HttpService();
  Map<String, dynamic>? _userProfile;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  void _loadProfile() async {
    try {
      final data = await _httpService.getMe();
      if (!mounted) return;
      if (data.containsKey('full_name')) { // if backend returns user directly
        setState(() => _userProfile = data);
      } else if (data.containsKey('user')) {
        setState(() => _userProfile = data['user']);
      }
    } catch (e) {
      // Ignore or show error
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _logout() async {
    await Supabase.instance.client.auth.signOut();
    // Navigator logic handled by onAuthStateChange listener
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Center(child: CircularProgressIndicator(color: const Color(0xFF075E54)));
    }

    if (_userProfile == null) {
      return Center(child: Text("Failed to load profile."));
    }

    return SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Center(
        child: Container(
          constraints: BoxConstraints(maxWidth: 400),
          child: Column(
            children: [
              CircleAvatar(
                radius: 50,
                backgroundColor: const Color(0xFF128C7E),
                child: Icon(Icons.person, size: 50, color: Colors.white),
              ),
              SizedBox(height: 24),
              _buildInfoRow(Icons.badge, "Name", _userProfile!['full_name'] ?? 'N/A'),
              Divider(),
              _buildInfoRow(Icons.email, "Email", _userProfile!['email'] ?? 'N/A'),
              Divider(),
              _buildInfoRow(Icons.phone, "Phone", _userProfile!['phone'] ?? 'N/A'),
              Divider(),
              _buildInfoRow(Icons.admin_panel_settings, "Role", _userProfile!['role'] ?? 'user'),
              SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _logout,
                  icon: Icon(Icons.logout, color: Colors.red),
                  label: Text("Logout", style: TextStyle(color: Colors.red)),
                  style: OutlinedButton.styleFrom(
                    padding: EdgeInsets.symmetric(vertical: 16),
                    side: BorderSide(color: Colors.red),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12.0),
      child: Row(
        children: [
          Icon(icon, color: Colors.grey[600]),
          SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
              SizedBox(height: 4),
              Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
            ],
          ),
        ],
      ),
    );
  }
}
