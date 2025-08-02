#!/usr/bin/env fish
# Fish Shell Setup for AI Command Tool

function setup_aicmd_fish
    echo "🐠 Setting up AI Command Tool for Fish Shell..."
    
    # Create aicmd config directory
    set config_dir ~/.aicmd
    mkdir -p $config_dir
    
    # Create fish integration file
    set fish_integration $config_dir/fish_integration.fish
    
    echo "# AI Command Tool Integration for Fish" > $fish_integration
    echo "set -gx AICMD_SHELL fish" >> $fish_integration
    echo "" >> $fish_integration
    
    echo "# Function to capture command errors using fish's event system" >> $fish_integration
    echo "function aicmd_capture_error --on-event fish_postexec" >> $fish_integration
    echo "    set -l exit_code \$status" >> $fish_integration
    echo "    set -l last_command \$argv[1]" >> $fish_integration
    echo "" >> $fish_integration
    echo "    if test \$exit_code -ne 0 -a -n \"\$last_command\"" >> $fish_integration
    echo "        # Create error message" >> $fish_integration
    echo "        set -l error_msg \"Command '\$last_command' failed with exit code \$exit_code\"" >> $fish_integration
    echo "" >> $fish_integration
    echo "        # Save to temporary file for aicmd to detect" >> $fish_integration
    echo "        echo \"\$error_msg\" > /tmp/aicmd_last_error" >> $fish_integration
    echo "        echo \"\$last_command\" > /tmp/aicmd_last_command" >> $fish_integration
    echo "        echo \"\$exit_code\" > /tmp/aicmd_last_exit_code" >> $fish_integration
    echo "" >> $fish_integration
    echo "        # Show hint if auto-suggest is enabled" >> $fish_integration
    echo "        if test \"\$AICMD_AUTO_SUGGEST\" = \"1\"" >> $fish_integration
    echo "            echo \"💡 Tip: Run 'aicmd fix' to get help with this error\"" >> $fish_integration
    echo "        end" >> $fish_integration
    echo "    end" >> $fish_integration
    echo "end" >> $fish_integration
    echo "" >> $fish_integration
    
    echo "# Enhanced command not found handler for Fish" >> $fish_integration
    echo "function fish_command_not_found" >> $fish_integration
    echo "    set -l cmd \$argv[1]" >> $fish_integration
    echo "    set -l remaining_args \$argv[2..-1]" >> $fish_integration
    echo "" >> $fish_integration
    echo "    # Build full command string" >> $fish_integration
    echo "    if test (count \$remaining_args) -gt 0" >> $fish_integration
    echo "        set -l full_command \"\$cmd \"(string join \" \" \$remaining_args)" >> $fish_integration
    echo "        echo \"fish: Unknown command: \$cmd (full command: \$full_command)\" > /tmp/aicmd_last_error" >> $fish_integration
    echo "        echo \"\$full_command\" > /tmp/aicmd_last_command" >> $fish_integration
    echo "    else" >> $fish_integration
    echo "        echo \"fish: Unknown command: \$cmd\" > /tmp/aicmd_last_error" >> $fish_integration
    echo "        echo \"\$cmd\" > /tmp/aicmd_last_command" >> $fish_integration
    echo "    end" >> $fish_integration
    echo "" >> $fish_integration
    echo "    echo \"127\" > /tmp/aicmd_last_exit_code" >> $fish_integration
    echo "" >> $fish_integration
    echo "    # Create simple error format for better detection" >> $fish_integration
    echo "    echo \"Command '\$cmd' not found\" > /tmp/aicmd_simple_error" >> $fish_integration
    echo "" >> $fish_integration
    echo "    if test \"\$AICMD_AUTO_SUGGEST\" = \"1\"" >> $fish_integration
    echo "        echo \"💡 Tip: Run 'aicmd fix' to get help finding this command\"" >> $fish_integration
    echo "    end" >> $fish_integration
    echo "" >> $fish_integration
    echo "    echo \"fish: Unknown command: \$cmd\"" >> $fish_integration
    echo "end" >> $fish_integration
    echo "" >> $fish_integration
    
    echo "# Fish-specific function to handle command completion errors" >> $fish_integration
    echo "function aicmd_preexec --on-event fish_preexec" >> $fish_integration
    echo "    # Store the command that's about to be executed" >> $fish_integration
    echo "    echo \"\$argv\" > /tmp/aicmd_current_command" >> $fish_integration
    echo "end" >> $fish_integration
    echo "" >> $fish_integration

    echo "function aicmd-status" >> $fish_integration
    echo "    if test -f /tmp/aicmd_last_error" >> $fish_integration
    echo "        echo \"📋 Last Error Info:\"" >> $fish_integration
    echo "        cat /tmp/aicmd_last_error" >> $fish_integration
    echo "    else" >> $fish_integration
    echo "        echo \"✅ No recent errors found\"" >> $fish_integration
    echo "    end" >> $fish_integration
    echo "end" >> $fish_integration
    echo "" >> $fish_integration
    
    echo "# Fish-specific aliases for convenience" >> $fish_integration
    echo "alias aicmd-enable-auto 'set -gx AICMD_AUTO_SUGGEST 1'" >> $fish_integration
    echo "alias aicmd-disable-auto 'set -e AICMD_AUTO_SUGGEST'" >> $fish_integration
    echo "" >> $fish_integration
    
    echo "✓ Created Fish integration file: $fish_integration"
    
    # Check if config.fish exists
    set fish_config ~/.config/fish/config.fish
    if test -f $fish_config
        echo "✓ Found Fish config file: $fish_config"
        
        # Check if integration is already sourced
        if grep -q "aicmd" $fish_config
            echo "⚠ AI Command Tool integration already exists in config.fish"
        else
            echo ""
            echo "📝 To enable the integration, add this line to your $fish_config:"
            echo ""
            echo "source $fish_integration"
            echo ""
            echo "Or run this command:"
            echo "echo 'source $fish_integration' >> $fish_config"
        end
    else
        echo "⚠ Fish config file not found. Creating it..."
        mkdir -p (dirname $fish_config)
        echo "# Fish configuration" > $fish_config
        echo "source $fish_integration" >> $fish_config
        echo "✓ Created $fish_config with aicmd integration"
    end
    
    echo ""
    echo "🎯 To test the setup:"
    echo "1. Restart your Fish shell or run: source $fish_integration"
    echo "2. Enable auto-suggestions: set -gx AICMD_AUTO_SUGGEST 1"
    echo "3. Try a typo: lls"
    echo "4. Then run: aicmd fix"
    echo ""
    echo "🔧 Fish-specific commands:"
    echo "- aicmd-enable-auto   # Enable auto suggestions"
    echo "- aicmd-disable-auto  # Disable auto suggestions"
    echo ""
end

# Run the setup
setup_aicmd_fish
