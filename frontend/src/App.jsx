import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Notifications from './pages/Notifications';
import GrassrootIdeaSubmission from './pages/GrassrootIdeaSubmission';
import PostChallenge from './pages/PostChallenge';
import ManagementDashboard from './pages/ManagementDashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="submit-grassroot" element={<GrassrootIdeaSubmission />} />
          <Route path="post-challenge" element={<PostChallenge />} />
          <Route path="management" element={<ManagementDashboard />} />
          {/* Add more routes as we go */}
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
