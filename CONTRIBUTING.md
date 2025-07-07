# 🤝 Contributing to Trading Algorithm Model

Thank you for your interest in contributing to our AI-powered trading system! This document provides guidelines for contributing to the project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- OpenAI API key
- Polygon.io API key

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/trading-algorithm-model.git
   cd trading-algorithm-model
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up configuration**
   ```bash
   cp core/config.example.py core/config.py
   # Edit core/config.py with your API keys
   ```

## 🔧 Development Setup

### Project Structure

```
live_trading_system/
├── core/                    # Core trading components
│   ├── complete_trading_system.py
│   ├── hybrid_trading_system.py
│   ├── bias_analyzer.py
│   ├── fvg_detector.py
│   ├── cisd_3m_analyzer.py
│   ├── fvg_visualizer.py
│   └── config.py
├── data/                    # Data storage
├── logs/                    # Trading logs
├── tests/                   # Test files
├── docs/                    # Documentation
└── examples/                # Example usage
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core

# Run specific test file
pytest tests/test_bias_analyzer.py
```

## 📝 Code Style

We follow PEP 8 style guidelines. Use the following tools:

### Code Formatting

```bash
# Format code with black
black core/ tests/

# Check code style
flake8 core/ tests/
```

### Type Hints

Use type hints for function parameters and return values:

```python
def analyze_bias(data: pd.DataFrame) -> Dict[str, Any]:
    """Analyze market bias from price data."""
    pass
```

### Documentation

- Use docstrings for all functions and classes
- Follow Google docstring format
- Include examples for complex functions

## 🧪 Testing

### Writing Tests

1. **Test files should be in the `tests/` directory**
2. **Use descriptive test names**
3. **Test both success and failure cases**
4. **Mock external API calls**

Example test:

```python
import pytest
from unittest.mock import patch
from core.bias_analyzer import label_bias

def test_label_bias_with_valid_data():
    """Test bias labeling with valid market data."""
    # Arrange
    test_data = create_test_data()
    
    # Act
    result = label_bias(test_data)
    
    # Assert
    assert len(result) > 0
    assert 'Bias' in result.columns
```

### Test Categories

- **Unit Tests**: Test individual functions
- **Integration Tests**: Test component interactions
- **API Tests**: Test external API integrations
- **Performance Tests**: Test system performance

## 🔄 Pull Request Process

### Before Submitting

1. **Ensure tests pass**
   ```bash
   pytest
   ```

2. **Format your code**
   ```bash
   black core/ tests/
   flake8 core/ tests/
   ```

3. **Update documentation**
   - Update README.md if needed
   - Add docstrings for new functions
   - Update examples if applicable

### Pull Request Guidelines

1. **Create a descriptive title**
   - Use present tense: "Add feature" not "Added feature"
   - Be specific about the change

2. **Write a detailed description**
   ```markdown
   ## Description
   Brief description of the changes

   ## Changes Made
   - List specific changes
   - Include any breaking changes

   ## Testing
   - How to test the changes
   - Test results

   ## Screenshots (if applicable)
   ```

3. **Link related issues**
   - Use keywords like "Fixes #123" or "Closes #456"

### Review Process

1. **Automated checks must pass**
   - Tests
   - Code formatting
   - Documentation

2. **Code review required**
   - At least one maintainer approval
   - Address all review comments

3. **Merge after approval**
   - Squash commits if needed
   - Use conventional commit messages

## 🐛 Reporting Issues

### Bug Reports

Use the bug report template and include:

- **Clear description** of the issue
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages and logs**

### Security Issues

For security vulnerabilities:

1. **Do not open a public issue**
2. **Email security@yourdomain.com**
3. **Include detailed information**
4. **Wait for response before disclosure**

## 💡 Feature Requests

### Before Submitting

1. **Check existing issues** for similar requests
2. **Search documentation** for existing features
3. **Consider the scope** and impact

### Feature Request Template

```markdown
## Feature Description
Brief description of the requested feature

## Use Case
How would this feature be used?

## Proposed Implementation
Any ideas for implementation?

## Alternatives Considered
Other approaches you've considered
```

## 🏷️ Labels and Milestones

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `question`: Further information is requested

### Milestones

- `v1.0.0`: Initial stable release
- `v1.1.0`: Minor features and improvements
- `v2.0.0`: Major version with breaking changes

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: For security issues

### Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Help others learn and grow
- Follow the project's coding standards

## 🎉 Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **Release notes** for significant contributions
- **GitHub contributors** page

---

Thank you for contributing to our trading algorithm project! 🚀 